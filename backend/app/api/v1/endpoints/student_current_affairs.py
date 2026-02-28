"""
Student Current Affairs endpoints — /api/v1/student/current-affairs
====================================================================
GET  /                — feed with is_included_in_prediction badge + learned state
POST /:id/learned     — mark an item as learned (stored in user.learning_progress)
"""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DBSession, get_current_user
from app.models.current_affair import CurrentAffairsItem
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Response schemas (student-facing, enriched) ──────────────

class StudentCAItem(BaseModel):
    id: str
    headline: str
    summary: str | None = None
    content: str
    category: str
    source_name: str | None = None
    source_url: str | None = None
    published_date: str | None = None
    relevance_score: float = 0.0

    # MCQ fields
    mcq_generated: bool = False
    mcq_text: str | None = None
    mcq_options: dict | None = None
    mcq_correct_answer: str | None = None
    mcq_explanation: str | None = None

    # Enriched
    is_included_in_prediction: bool = False
    is_learned: bool = False


class StudentCAListResponse(BaseModel):
    items: list[StudentCAItem] = []
    total: int = 0
    page: int = 1
    per_page: int = 20
    categories: list[str] = []


class LearnedResponse(BaseModel):
    message: str = "Marked as learned"
    article_id: str
    is_learned: bool = True


# ── Helpers ──────────────────────────────────────────────────

def _get_learned_ids(user: User) -> set[str]:
    """Extract the set of learned CA item IDs from user.learning_progress JSON."""
    progress = user.learning_progress or {}
    return set(progress.get("learned_ca_ids", []))


# ── GET /student/current-affairs ─────────────────────────────

@router.get(
    "/current-affairs",
    response_model=StudentCAListResponse,
    summary="Student current-affairs feed",
)
async def student_current_affairs_feed(
    db: DBSession,
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: str | None = Query(
        None,
        description="Filter: government, sports, science, economy, international, records, or all",
    ),
    target_date: date | None = Query(
        None,
        description="Specific date. Defaults to today with 7-day fallback.",
    ),
):
    """Return today's approved current affairs feed for students.

    Items marked ``is_included_in_prediction = True`` carry a star badge.
    Items previously marked as "learned" are flagged via ``is_learned``.
    Sorted: prediction-included first, then by relevance_score desc.
    """
    from datetime import timedelta

    target = target_date or date.today()
    fallback_start = target - timedelta(days=7)

    conditions = [
        CurrentAffairsItem.is_approved.is_(True),
        or_(
            CurrentAffairsItem.published_date == target,
            and_(
                CurrentAffairsItem.published_date >= fallback_start,
                CurrentAffairsItem.published_date <= target,
            ),
        ),
    ]

    # Map friendly category names to DB values
    category_map: dict[str, str] = {
        "government": "govt_appointment",
        "sports": "sports",
        "science": "science",
        "economy": "economy",
        "international": "international",
        "records": "records",
    }

    if category and category.lower() != "all":
        db_category = category_map.get(category.lower(), category.lower())
        conditions.append(CurrentAffairsItem.category == db_category)

    where = and_(*conditions)
    skip = (page - 1) * per_page

    # Count
    count_q = select(func.count()).select_from(CurrentAffairsItem).where(where)
    total: int = (await db.execute(count_q)).scalar() or 0

    # Fetch items
    query = (
        select(CurrentAffairsItem)
        .where(where)
        .order_by(
            CurrentAffairsItem.is_included_in_prediction.desc(),
            CurrentAffairsItem.relevance_score.desc(),
            CurrentAffairsItem.published_date.desc().nullslast(),
        )
        .offset(skip)
        .limit(per_page)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    # Distinct categories for filter tabs
    cat_q = (
        select(CurrentAffairsItem.category)
        .where(where)
        .distinct()
    )
    cat_result = await db.execute(cat_q)
    categories = sorted([r[0] for r in cat_result.all() if r[0]])

    # Learned IDs
    learned_ids = _get_learned_ids(current_user)

    response_items: list[StudentCAItem] = []
    for item in items:
        response_items.append(StudentCAItem(
            id=str(item.id),
            headline=item.headline,
            summary=item.summary,
            content=item.content,
            category=item.category,
            source_name=item.source_name,
            source_url=item.source_url,
            published_date=item.published_date.isoformat() if item.published_date else None,
            relevance_score=item.relevance_score,
            mcq_generated=item.mcq_generated,
            mcq_text=item.mcq_text,
            mcq_options=item.mcq_options,
            mcq_correct_answer=item.mcq_correct_answer,
            mcq_explanation=item.mcq_explanation,
            is_included_in_prediction=item.is_included_in_prediction,
            is_learned=str(item.id) in learned_ids,
        ))

    return StudentCAListResponse(
        items=response_items,
        total=total,
        page=page,
        per_page=per_page,
        categories=categories,
    )


# ── POST /student/current-affairs/:id/learned ────────────────

@router.post(
    "/current-affairs/{article_id}/learned",
    response_model=LearnedResponse,
    summary="Mark a current affairs item as learned",
)
async def mark_as_learned(
    article_id: UUID,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Toggle the 'learned' state for a current affairs item.

    Stored in user.learning_progress JSON under the key ``learned_ca_ids``.
    Calling again on an already-learned item will un-learn it (toggle).
    """
    # Verify article exists
    article = await db.get(CurrentAffairsItem, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    # Read current progress
    progress = dict(current_user.learning_progress or {})
    learned_ids: list[str] = list(progress.get("learned_ca_ids", []))

    article_str = str(article_id)
    is_learned: bool

    if article_str in learned_ids:
        learned_ids.remove(article_str)
        is_learned = False
    else:
        learned_ids.append(article_str)
        is_learned = True

    progress["learned_ca_ids"] = learned_ids
    current_user.learning_progress = progress

    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)

    return LearnedResponse(
        message="Marked as learned" if is_learned else "Unmarked as learned",
        article_id=article_str,
        is_learned=is_learned,
    )
