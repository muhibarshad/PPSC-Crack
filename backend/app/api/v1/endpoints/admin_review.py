"""
Admin Review Queue Endpoints
==============================
GET  /api/v1/admin/review-queue           — list questions needing review
GET  /api/v1/admin/review-queue/stats     — review queue statistics
PUT  /api/v1/admin/questions/{id}         — correct a question + re-embed
PUT  /api/v1/admin/questions/{id}/approve — quick-approve (mark reviewed)
PUT  /api/v1/admin/questions/{id}/reject  — reject / delete question
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.dependencies import DBSession, OpenAI, require_admin
from app.crud.crud_question import crud_question
from app.models.question import Question
from app.models.paper import Paper
from app.models.topic import Topic
from app.models.user import User
from app.schemas.review_queue import (
    ReviewQueueItem,
    ReviewQueueResponse,
    QuestionCorrection,
    QuestionCorrectionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────

def _build_review_item(q: Question) -> ReviewQueueItem:
    """Map a Question ORM object (with eager-loaded relations) to ReviewQueueItem."""
    paper = q.paper_rel
    topic = q.topic_rel

    return ReviewQueueItem(
        id=q.id,
        paper_id=q.paper_id,
        question_number=q.question_number,
        question_text=q.question_text,
        option_a=q.option_a,
        option_b=q.option_b,
        option_c=q.option_c,
        option_d=q.option_d,
        correct_answer=q.correct_answer,
        topic_id=q.topic_id,
        subtopic=q.subtopic,
        difficulty_score=q.difficulty_score,
        fact_extracted=q.fact_extracted,
        year_appeared=q.year_appeared,
        is_repeated=q.is_repeated,
        repeat_count=q.repeat_count,
        similarity_group_id=q.similarity_group_id,
        needs_review=q.needs_review,
        admin_notes=q.admin_notes,
        created_at=q.created_at,
        # Paper context
        paper_title=paper.title if paper else "Unknown Paper",
        paper_year=paper.paper_year if paper else 0,
        paper_month=paper.paper_month if paper else None,
        job_type_name=(
            paper.job_type_rel.name if paper and paper.job_type_rel else None
        ),
        raw_scan_data=paper.raw_scan_data if paper else None,
        # Topic context
        topic_name=topic.name if topic else None,
        topic_display_name=topic.display_name if topic else None,
    )


# ── GET /review-queue ───────────────────────────────────────

@router.get(
    "/review-queue",
    response_model=ReviewQueueResponse,
    summary="List questions needing admin review",
    description=(
        "Returns paginated questions flagged with `needs_review=True`, "
        "enriched with paper and topic context for the admin UI."
    ),
)
async def get_review_queue(
    db: DBSession,
    admin: User = Depends(require_admin),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
    paper_id: UUID | None = Query(None, description="Filter by paper"),
    topic_id: UUID | None = Query(None, description="Filter by topic"),
):
    """Fetch the review queue with optional filters."""

    # Build base query with eager-loaded relationships
    base = (
        select(Question)
        .where(Question.needs_review.is_(True))
        .options(
            selectinload(Question.paper_rel).selectinload(Paper.job_type_rel),
            selectinload(Question.topic_rel),
        )
    )

    # Optional filters
    if paper_id:
        base = base.where(Question.paper_id == paper_id)
    if topic_id:
        base = base.where(Question.topic_id == topic_id)

    # Count total
    count_q = (
        select(func.count())
        .select_from(Question)
        .where(Question.needs_review.is_(True))
    )
    if paper_id:
        count_q = count_q.where(Question.paper_id == paper_id)
    if topic_id:
        count_q = count_q.where(Question.topic_id == topic_id)

    total: int = (await db.execute(count_q)).scalar() or 0

    # Paginated results
    offset = (page - 1) * per_page
    result = await db.execute(
        base.order_by(Question.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    questions = result.scalars().all()

    items = [_build_review_item(q) for q in questions]

    return ReviewQueueResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


# ── GET /review-queue/stats ─────────────────────────────────

@router.get(
    "/review-queue/stats",
    summary="Review queue statistics",
)
async def get_review_stats(
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Quick stats for the review queue dashboard."""

    total_pending = (
        await db.execute(
            select(func.count())
            .select_from(Question)
            .where(Question.needs_review.is_(True))
        )
    ).scalar() or 0

    total_reviewed = (
        await db.execute(
            select(func.count())
            .select_from(Question)
            .where(Question.needs_review.is_(False))
        )
    ).scalar() or 0

    # Breakdown by paper
    by_paper_q = (
        select(
            Paper.id,
            Paper.title,
            Paper.paper_year,
            func.count(Question.id).label("pending_count"),
        )
        .join(Question, Question.paper_id == Paper.id)
        .where(Question.needs_review.is_(True))
        .group_by(Paper.id, Paper.title, Paper.paper_year)
        .order_by(func.count(Question.id).desc())
        .limit(20)
    )
    by_paper_result = await db.execute(by_paper_q)
    by_paper = [
        {
            "paper_id": str(row.id),
            "title": row.title,
            "paper_year": row.paper_year,
            "pending_count": row.pending_count,
        }
        for row in by_paper_result.all()
    ]

    return {
        "total_pending": total_pending,
        "total_reviewed": total_reviewed,
        "by_paper": by_paper,
    }


# ── PUT /questions/{id} — Correct a question ────────────────

@router.put(
    "/questions/{question_id}",
    response_model=QuestionCorrectionResponse,
    summary="Correct a question and re-embed",
    description=(
        "Admin corrects question text, answer, options, or topic. "
        "Sets `needs_review=False` and triggers a new embedding for the "
        "updated text via OpenAI."
    ),
)
async def correct_question(
    question_id: UUID,
    body: QuestionCorrection,
    db: DBSession,
    openai: OpenAI,
    admin: User = Depends(require_admin),
):
    """Apply admin corrections, clear review flag, re-embed."""

    # 1. Fetch the question
    question = await crud_question.get_or_404(db, id=question_id)

    # 2. Build update dict from non-None fields
    update_data: dict = {}
    correction_fields = body.model_dump(exclude_none=True)
    update_data.update(correction_fields)

    # Always mark as reviewed after correction
    update_data["needs_review"] = False

    # If admin didn't supply notes, auto-generate
    if "admin_notes" not in update_data:
        changed = ", ".join(correction_fields.keys()) or "approved"
        update_data["admin_notes"] = f"Corrected by admin: {changed}"

    # 3. Apply the update
    updated = await crud_question.update(db, id=question_id, obj_in=update_data)
    await db.commit()

    # 4. Re-embed if text was changed (question_text or options)
    embedding_updated = False
    text_fields_changed = any(
        k in correction_fields
        for k in ("question_text", "option_a", "option_b", "option_c", "option_d")
    )

    if text_fields_changed:
        try:
            # Build the full text to embed (same format as ingestion pipeline)
            embed_text = _build_embed_text(updated)
            embedding = await openai.embed_single(embed_text)
            await crud_question.set_embedding(db, id=question_id, embedding=embedding)
            await db.commit()
            embedding_updated = True
            logger.info(
                "Re-embedded question %s after admin correction", question_id
            )
        except Exception as exc:
            logger.warning(
                "Failed to re-embed question %s: %s (will retry later)",
                question_id, exc,
            )

    return QuestionCorrectionResponse(
        id=updated.id,
        needs_review=updated.needs_review,
        admin_notes=updated.admin_notes,
        embedding_updated=embedding_updated,
        message=(
            "Question corrected and re-embedded"
            if embedding_updated
            else "Question corrected"
        ),
    )


# ── PUT /questions/{id}/approve — Quick approve ─────────────

@router.put(
    "/questions/{question_id}/approve",
    response_model=QuestionCorrectionResponse,
    summary="Quick-approve a question",
)
async def approve_question(
    question_id: UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
    notes: str | None = Query(None, description="Optional review notes"),
):
    """Mark a question as reviewed without changes."""
    updated = await crud_question.mark_reviewed(db, id=question_id, notes=notes)
    await db.commit()

    return QuestionCorrectionResponse(
        id=updated.id,
        needs_review=False,
        admin_notes=updated.admin_notes,
        embedding_updated=False,
        message="Question approved",
    )


# ── DELETE /questions/{id} — Reject / remove ────────────────

@router.delete(
    "/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reject and delete a question",
)
async def reject_question(
    question_id: UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Remove a question that was parsed incorrectly or is garbage."""
    await crud_question.get_or_404(db, id=question_id)
    await crud_question.delete(db, id=question_id)
    await db.commit()
    logger.info("Admin deleted question %s", question_id)


# ── Internal helpers ─────────────────────────────────────────

def _build_embed_text(q: Question) -> str:
    """Build the text string to send to the embedding model.

    Same format as the ingestion pipeline so vectors are comparable.
    """
    parts = [q.question_text]
    for opt_label, opt_val in [
        ("A", q.option_a),
        ("B", q.option_b),
        ("C", q.option_c),
        ("D", q.option_d),
    ]:
        if opt_val:
            parts.append(f"({opt_label}) {opt_val}")
    return " ".join(parts)
