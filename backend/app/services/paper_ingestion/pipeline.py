"""
Paper Ingestion Pipeline Orchestrator
=======================================
Runs the full 9-step ingestion pipeline.
Steps 1-3 run synchronously (fast parsing).
Steps 4-8 run as a Celery background task.
Step 9 returns the summary to the admin.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper
from app.models.question import Question
from app.services.openai.client import OpenAIService, get_openai_service
from app.services.paper_ingestion import (
    ParsedQuestion,
    parse_questions_text,
    parse_answer_key,
    map_questions_to_answers,
)
from app.services.paper_ingestion.classification import classify_questions, resolve_topic_ids
from app.services.paper_ingestion.fact_extraction import extract_facts
from app.services.paper_ingestion.embeddings import generate_and_store_embeddings, check_similarity
from app.services.paper_ingestion.pattern_update import update_topic_frequencies

logger = logging.getLogger(__name__)


def _question_to_dict(q: ParsedQuestion) -> dict:
    """Convert a ``ParsedQuestion`` dataclass to a plain dict."""
    return {
        "question_number": q.question_number,
        "question_text": q.question_text,
        "option_a": q.option_a,
        "option_b": q.option_b,
        "option_c": q.option_c,
        "option_d": q.option_d,
        "correct_answer": q.correct_answer,
    }


async def run_sync_steps(
    db: AsyncSession,
    *,
    paper_id: UUID,
    job_type_id: UUID,
    paper_year: int,
    paper_month: int | None,
    title: str,
    questions_text: str,
    answer_key_text: str,
) -> dict:
    """Steps 1-3: Parse, map, and persist raw question rows.

    Returns a summary dict and the list of created Question ORM objects.
    This runs inside the request lifecycle (fast, no AI calls).
    """
    start = time.time()

    # ── Step 1: Parse questions ──────────────────────────────
    parsed_questions = parse_questions_text(questions_text)

    # ── Step 2: Parse answer key ─────────────────────────────
    answer_map = parse_answer_key(answer_key_text)

    # ── Step 3: Map Q&A ──────────────────────────────────────
    parse_result = map_questions_to_answers(parsed_questions, answer_map)

    # ── Persist Paper row ────────────────────────────────────
    paper = Paper(
        id=paper_id,
        job_type_id=job_type_id,
        paper_year=paper_year,
        paper_month=paper_month,
        title=title,
        paper_date=datetime(paper_year, paper_month or 1, 1, tzinfo=timezone.utc),
        total_questions=len(parse_result.questions),
        ingestion_status="processing",
    )
    db.add(paper)
    await db.flush()

    # ── Persist Question rows (without AI fields yet) ────────
    question_records: list[Question] = []
    for q in parse_result.questions:
        record = Question(
            paper_id=paper_id,
            question_number=q.question_number,
            question_text=q.question_text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            correct_answer=q.correct_answer,
            year_appeared=paper_year,
            needs_review=q.needs_review,
            admin_notes=q.review_reason,
        )
        db.add(record)
        question_records.append(record)

    await db.flush()
    # Refresh to get generated IDs
    for r in question_records:
        await db.refresh(r)

    await db.commit()

    elapsed = time.time() - start
    summary = {
        "paper_id": str(paper_id),
        "total_parsed": parse_result.total_parsed,
        "total_mapped": parse_result.total_mapped,
        "unmapped_questions": parse_result.unmapped_questions,
        "unmapped_answers": parse_result.unmapped_answers,
        "warnings": parse_result.warnings,
        "sync_processing_time_ms": round(elapsed * 1000, 2),
    }

    logger.info("Sync steps complete for paper %s in %.0fms", paper_id, elapsed * 1000)
    return summary


async def run_ai_steps(
    db: AsyncSession,
    *,
    paper_id: UUID,
    job_type_id: UUID,
    paper_year: int,
) -> dict:
    """Steps 4-8: AI-powered processing (runs in background).

    4. Topic classification
    5. Fact extraction
    6. Embedding generation
    7. Similarity check
    8. Pattern update
    """
    start = time.time()
    openai_svc = get_openai_service()
    ai_summary: dict = {"paper_id": str(paper_id), "steps": {}}

    try:
        # Load question records from DB
        from sqlalchemy import select
        result = await db.execute(
            select(Question)
            .where(Question.paper_id == paper_id)
            .order_by(Question.question_number)
        )
        question_records = list(result.scalars().all())

        if not question_records:
            logger.error("No questions found for paper %s", paper_id)
            await _set_paper_status(db, paper_id, "failed")
            return {"error": "No questions found"}

        # Build dicts for AI services
        q_dicts = [
            {
                "question_number": q.question_number,
                "question_text": q.question_text,
                "option_a": q.option_a,
                "option_b": q.option_b,
                "option_c": q.option_c,
                "option_d": q.option_d,
                "correct_answer": q.correct_answer,
            }
            for q in question_records
        ]

        total_questions = len(question_records)

        # ── Step 4: Topic Classification ─────────────────────
        logger.info("[Paper %s] Step 4: Topic classification…", paper_id)
        t4 = time.time()
        classifications = await classify_questions(db, openai_svc, q_dicts)
        topic_map = await resolve_topic_ids(db, classifications)

        # Apply topics to question records
        classified_count = 0
        for q_rec in question_records:
            if q_rec.question_number in topic_map:
                topic_id, subtopic = topic_map[q_rec.question_number]
                q_rec.topic_id = topic_id
                q_rec.subtopic = subtopic
                classified_count += 1
                db.add(q_rec)

        await db.flush()
        ai_summary["steps"]["classification"] = {
            "classified": classified_count,
            "total": total_questions,
            "new_topics": sum(1 for c in classifications if c.get("is_new_topic")),
            "time_ms": round((time.time() - t4) * 1000, 2),
        }

        # ── Step 5: Fact Extraction ──────────────────────────
        logger.info("[Paper %s] Step 5: Fact extraction…", paper_id)
        t5 = time.time()
        facts = await extract_facts(openai_svc, q_dicts)

        for q_rec in question_records:
            fact = facts.get(q_rec.question_number)
            if fact:
                q_rec.fact_extracted = fact
                db.add(q_rec)

        await db.flush()
        ai_summary["steps"]["fact_extraction"] = {
            "extracted": len(facts),
            "total": total_questions,
            "time_ms": round((time.time() - t5) * 1000, 2),
        }

        # ── Step 6: Embedding Generation ─────────────────────
        logger.info("[Paper %s] Step 6: Embedding generation…", paper_id)
        t6 = time.time()
        embeddings = await generate_and_store_embeddings(
            db, openai_svc, question_records, q_dicts,
        )
        ai_summary["steps"]["embeddings"] = {
            "generated": len(embeddings),
            "time_ms": round((time.time() - t6) * 1000, 2),
        }

        # ── Step 7: Similarity Check ─────────────────────────
        logger.info("[Paper %s] Step 7: Similarity check…", paper_id)
        t7 = time.time()
        sim_result = await check_similarity(
            db, question_records, embeddings, exclude_paper_id=paper_id,
        )
        ai_summary["steps"]["similarity"] = {
            "duplicates_found": sim_result["duplicates_found"],
            "details": sim_result["details"][:20],  # cap for summary
            "time_ms": round((time.time() - t7) * 1000, 2),
        }

        # ── Step 8: Pattern Update ───────────────────────────
        logger.info("[Paper %s] Step 8: Pattern update…", paper_id)
        t8 = time.time()
        pattern_result = await update_topic_frequencies(
            db,
            paper_id=paper_id,
            job_type_id=job_type_id,
            paper_year=paper_year,
            total_questions=total_questions,
        )
        ai_summary["steps"]["pattern_update"] = {
            **pattern_result,
            "time_ms": round((time.time() - t8) * 1000, 2),
        }

        # ── Mark paper complete ──────────────────────────────
        await _set_paper_status(db, paper_id, "completed")
        await db.commit()

        total_elapsed = time.time() - start
        ai_summary["total_ai_processing_time_ms"] = round(total_elapsed * 1000, 2)
        ai_summary["status"] = "completed"

        logger.info(
            "[Paper %s] AI pipeline complete in %.1fs", paper_id, total_elapsed,
        )

    except Exception as exc:
        logger.exception("[Paper %s] AI pipeline failed: %s", paper_id, exc)
        await db.rollback()
        await _set_paper_status(db, paper_id, "failed")
        await db.commit()
        ai_summary["status"] = "failed"
        ai_summary["error"] = str(exc)

    return ai_summary


async def _set_paper_status(db: AsyncSession, paper_id: UUID, status: str) -> None:
    """Update paper ingestion status."""
    paper = await db.get(Paper, paper_id)
    if paper:
        paper.ingestion_status = status
        db.add(paper)
        await db.flush()
