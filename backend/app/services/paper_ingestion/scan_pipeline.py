"""
Scan-Based Paper Ingestion Pipeline
=====================================
Handles the end-to-end flow for scanned paper images:

1. Upload images to S3/R2
2. OCR via GPT-4o Vision (questions + answers)
3. Map questions to answers with confidence gating
4. Persist paper + questions (low-confidence → needs_review=True)
5. Dispatch AI pipeline (steps 4-8) for high-confidence questions

This module provides:
- ``run_scan_sync_steps()``  — called during the request (upload + OCR + persist)
- ``run_scan_ai_steps()``    — called by Celery (classify, extract, embed…)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.paper import Paper
from app.models.question import Question
from app.services.openai.client import OpenAIService, get_openai_service
from app.services.paper_ingestion.ocr import (
    OCRQuestion,
    OCRAnswerMapping,
    OCRResult,
    run_full_ocr,
)

logger = logging.getLogger(__name__)


async def run_scan_sync_steps(
    db: AsyncSession,
    openai: OpenAIService,
    *,
    paper_id: UUID,
    job_type_id: UUID,
    paper_year: int,
    paper_month: int | None,
    title: str,
    image_urls: list[str],
    image_labels: list[str],
) -> dict:
    """Steps 1-3 for scan mode: OCR + map + persist.

    Runs inside the request lifecycle. The actual S3 upload happens
    before this function is called (in the endpoint handler).

    Parameters
    ----------
    image_urls:
        Public URLs of the uploaded scan images (already in S3/R2).
    image_labels:
        Labels like "questions_front", "questions_back", "answers_front", "answers_back".

    Returns
    -------
    dict
        Summary including OCR stats, question counts, and review counts.
    """
    start = time.time()
    confidence_threshold = settings.OCR_CONFIDENCE_THRESHOLD

    # ── Classify images by label ─────────────────────────────
    question_images: list[str] = []
    answer_images: list[str] = []

    for url, label in zip(image_urls, image_labels):
        label_lower = label.lower()
        if "answer" in label_lower or "key" in label_lower:
            answer_images.append(url)
        else:
            # Default: treat as question image
            question_images.append(url)

    if not question_images:
        raise ValueError("At least one question image is required")

    # ── Step 1: Run GPT-4o Vision OCR ────────────────────────
    logger.info("[Paper %s] Running Vision OCR on %d question + %d answer images...",
                paper_id, len(question_images), len(answer_images))

    ocr_result: OCRResult = await run_full_ocr(
        openai, question_images, answer_images,
    )

    if not ocr_result.questions:
        raise ValueError("OCR failed to extract any questions from the images")

    # ── Step 2: Map answers to questions ─────────────────────
    answer_map: dict[int, OCRAnswerMapping] = {
        a.question_number: a for a in ocr_result.answers
    }

    # ── Step 3: Build & persist Paper + Question rows ────────
    raw_scan_data = {
        "mode": "scan",
        "images": [
            {"url": url, "label": label}
            for url, label in zip(image_urls, image_labels)
        ],
        "ocr_stats": {
            "total_questions_extracted": len(ocr_result.questions),
            "total_answers_extracted": len(ocr_result.answers),
            "warnings": ocr_result.warnings,
        },
    }

    paper = Paper(
        id=paper_id,
        job_type_id=job_type_id,
        paper_year=paper_year,
        paper_month=paper_month,
        title=title,
        paper_date=datetime(paper_year, paper_month or 1, 1, tzinfo=timezone.utc),
        total_questions=len(ocr_result.questions),
        ingestion_status="processing",
        raw_scan_data=raw_scan_data,
    )
    db.add(paper)
    await db.flush()

    # Persist questions with confidence-based review flagging
    review_count = 0
    mapped_count = 0
    question_records: list[Question] = []

    for oq in ocr_result.questions:
        needs_review = False
        review_reasons: list[str] = []

        # Check OCR confidence
        if oq.confidence < confidence_threshold:
            needs_review = True
            review_reasons.append(
                f"OCR confidence {oq.confidence:.2f} < {confidence_threshold}"
            )

        # Check answer mapping
        correct_answer: str | None = None
        answer_entry = answer_map.get(oq.question_number)

        if answer_entry:
            correct_answer = answer_entry.correct_answer
            mapped_count += 1

            # Check answer confidence
            if answer_entry.confidence < confidence_threshold:
                needs_review = True
                review_reasons.append(
                    f"Answer OCR confidence {answer_entry.confidence:.2f} < {confidence_threshold}"
                )
        else:
            needs_review = True
            review_reasons.append("No answer mapping found")

        # Check for missing options
        if not oq.option_a or not oq.option_b:
            needs_review = True
            review_reasons.append("Missing options")

        # Check for empty/very short question text
        if len(oq.question_text.strip()) < 10:
            needs_review = True
            review_reasons.append("Question text too short or unclear")

        if needs_review:
            review_count += 1

        record = Question(
            paper_id=paper_id,
            question_number=oq.question_number,
            question_text=oq.question_text,
            option_a=oq.option_a,
            option_b=oq.option_b,
            option_c=oq.option_c,
            option_d=oq.option_d,
            correct_answer=correct_answer,
            year_appeared=paper_year,
            needs_review=needs_review,
            admin_notes="; ".join(review_reasons) if review_reasons else None,
        )
        db.add(record)
        question_records.append(record)

    await db.flush()
    for r in question_records:
        await db.refresh(r)

    await db.commit()

    elapsed = time.time() - start

    summary = {
        "paper_id": str(paper_id),
        "mode": "scan",
        "ocr_stats": {
            "questions_extracted": len(ocr_result.questions),
            "answers_extracted": len(ocr_result.answers),
            "answers_mapped": mapped_count,
            "unmapped_questions": [
                oq.question_number
                for oq in ocr_result.questions
                if oq.question_number not in answer_map
            ],
        },
        "review_stats": {
            "total_questions": len(ocr_result.questions),
            "needs_review": review_count,
            "auto_approved": len(ocr_result.questions) - review_count,
            "confidence_threshold": confidence_threshold,
        },
        "warnings": ocr_result.warnings,
        "sync_processing_time_ms": round(elapsed * 1000, 2),
    }

    logger.info(
        "[Paper %s] Scan sync steps complete: %d questions, %d need review (%.1fs)",
        paper_id, len(ocr_result.questions), review_count, elapsed,
    )
    return summary
