"""
Current Affairs — Student Endpoints
======================================
GET /api/v1/current-affairs          — today's feed for students
GET /api/v1/current-affairs/:id      — single article detail
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.crud import crud_current_affair
from app.dependencies import DBSession, require_student
from app.models.user import User
from app.schemas.current_affair import (
    CurrentAffairListResponse,
    CurrentAffairResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=CurrentAffairListResponse,
    summary="Today's current affairs feed (student)",
)
async def list_current_affairs(
    db: DBSession,
    _user: User = Depends(require_student),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: str | None = Query(
        None,
        description="Filter by category: govt_appointment, sports, science, economy, international, records",
    ),
    target_date: date | None = Query(
        None, description="Specific date (defaults to today). Falls back to last 7 days."
    ),
):
    """Return today's approved current affairs articles for students.

    Articles are sorted by relevance score (desc) and include MCQs when available.
    If no articles exist for today, falls back to the last 7 days.
    """
    skip = (page - 1) * per_page
    items, total = await crud_current_affair.get_student_feed(
        db,
        target_date=target_date,
        category=category,
        skip=skip,
        limit=per_page,
    )

    return CurrentAffairListResponse(
        items=[CurrentAffairResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get(
    "/{article_id}",
    response_model=CurrentAffairResponse,
    summary="Get a specific current affairs article",
)
async def get_article(
    article_id: UUID,
    db: DBSession,
    _user: User = Depends(require_student),
):
    """Get a single current affairs article by ID."""
    item = await crud_current_affair.get_or_404(db, id=article_id)
    return CurrentAffairResponse.model_validate(item)
