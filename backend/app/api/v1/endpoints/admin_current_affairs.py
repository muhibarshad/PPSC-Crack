"""
Current Affairs — Admin Endpoints
====================================
GET  /api/v1/admin/current-affairs              — admin view with scores
PUT  /api/v1/admin/current-affairs/:id/approve  — approve/reject item
POST /api/v1/admin/current-affairs/manual-add   — manually add an article
POST /api/v1/admin/current-affairs/refresh       — trigger manual feed refresh
GET  /api/v1/admin/current-affairs/stats         — daily stats
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.crud import crud_current_affair
from app.dependencies import DBSession, require_admin, OpenAI
from app.models.user import User
from app.models.current_affair import CurrentAffairsItem
from app.schemas.current_affair import (
    CurrentAffairAdminListResponse,
    CurrentAffairAdminResponse,
    CurrentAffairApprove,
    CurrentAffairManualAdd,
)
from app.services.ca_mcq_generator import generate_mcq_for_article

router = APIRouter()


@router.get(
    "/current-affairs",
    response_model=CurrentAffairAdminListResponse,
    summary="Admin current affairs feed with scoring details",
)
async def admin_list_current_affairs(
    db: DBSession,
    _admin: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    target_date: date | None = Query(None, description="Filter by date"),
    category: str | None = Query(None, description="Filter by category"),
    source_name: str | None = Query(None, description="Filter by source: dawn, geo, app"),
    is_approved: bool | None = Query(None, description="Filter by approval status"),
    min_relevance: float | None = Query(None, ge=0, le=1, description="Min relevance score"),
):
    """Return all current affairs articles with full scoring breakdown.

    Includes keyword_score, semantic_score, recency_score, category_score,
    approval workflow status, and MCQ details.
    """
    skip = (page - 1) * per_page
    items, total = await crud_current_affair.get_admin_feed(
        db,
        target_date=target_date,
        category=category,
        source_name=source_name,
        is_approved=is_approved,
        min_relevance=min_relevance,
        skip=skip,
        limit=per_page,
    )

    return CurrentAffairAdminListResponse(
        items=[CurrentAffairAdminResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.put(
    "/current-affairs/{article_id}/approve",
    response_model=CurrentAffairAdminResponse,
    summary="Approve or reject a current affairs item",
)
async def approve_current_affair(
    article_id: UUID,
    payload: CurrentAffairApprove,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Approve or reject a current affairs article.

    Approved articles become visible to students.
    Optionally flag for prediction inclusion.
    """
    item = await crud_current_affair.approve(
        db,
        id=article_id,
        is_approved=payload.is_approved,
        is_included_in_prediction=payload.is_included_in_prediction,
        approved_by=admin.id,
    )
    return CurrentAffairAdminResponse.model_validate(item)


@router.post(
    "/current-affairs/manual-add",
    response_model=CurrentAffairAdminResponse,
    status_code=201,
    summary="Manually add a current affairs article",
)
async def manual_add_current_affair(
    payload: CurrentAffairManualAdd,
    db: DBSession,
    admin: User = Depends(require_admin),
    openai: OpenAI = None,  # type: ignore[assignment]
):
    """Admin manually adds a current affairs article.

    Optionally generates an MCQ on the spot if generate_mcq=True.
    Article is auto-approved since admin is adding it directly.
    """
    from datetime import datetime, timezone

    item = CurrentAffairsItem(
        headline=payload.headline,
        content=payload.content,
        summary=payload.summary,
        category=payload.category,
        source_url=payload.source_url,
        published_date=payload.published_date or date.today(),
        source_name="manual",
        relevance_score=1.0,  # Manual adds are inherently relevant
        keyword_score=1.0,
        semantic_score=0.0,
        recency_score=1.0,
        category_score=1.0,
        is_approved=True,
        approved_by=admin.id,
        approved_at=datetime.now(timezone.utc),
    )

    # Generate embedding if OpenAI is available
    if openai:
        try:
            embedding = await openai.embed_single(
                f"{payload.headline}. {(payload.summary or payload.content)[:500]}"
            )
            item.embedding = embedding
        except Exception:
            pass  # Non-critical

    db.add(item)
    await db.flush()
    await db.refresh(item)

    # Optionally generate MCQ
    if payload.generate_mcq and openai:
        mcq_data = await generate_mcq_for_article(item, openai_svc=openai)
        if mcq_data:
            item.mcq_generated = True
            item.mcq_text = mcq_data["mcq_text"]
            item.mcq_options = mcq_data["mcq_options"]
            item.mcq_correct_answer = mcq_data["mcq_correct_answer"]
            item.mcq_explanation = mcq_data["mcq_explanation"]
            db.add(item)
            await db.flush()
            await db.refresh(item)

    return CurrentAffairAdminResponse.model_validate(item)


@router.post(
    "/current-affairs/refresh",
    summary="Trigger manual feed refresh",
)
async def trigger_manual_refresh(
    _admin: User = Depends(require_admin),
):
    """Trigger an immediate RSS feed refresh and scoring pipeline.

    Runs asynchronously via Celery. Returns the task ID for tracking.
    """
    from app.tasks.current_affairs_pipeline import run_manual_refresh

    task = run_manual_refresh.apply_async()
    return {
        "message": "Current affairs refresh triggered",
        "task_id": task.id,
    }


@router.get(
    "/current-affairs/stats",
    summary="Daily current affairs stats",
)
async def get_daily_stats(
    db: DBSession,
    _admin: User = Depends(require_admin),
    target_date: date | None = Query(None, description="Stats for date (default: today)"),
):
    """Return aggregate statistics for a given date."""
    return await crud_current_affair.get_daily_stats(db, target_date=target_date)
