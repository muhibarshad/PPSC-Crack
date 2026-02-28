"""
Predictions endpoints — published AI-powered exam predictions (student-facing).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.dependencies import DBSession, get_current_user
from app.crud.crud_prediction import crud_prediction
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionListResponse, PredictionResponse

router = APIRouter()


def _build_response(pred: Prediction) -> PredictionResponse:
    jt = pred.job_type_rel
    q_count = 0
    if pred.questions_json and isinstance(pred.questions_json, dict):
        q_count = len(pred.questions_json.get("questions", []))
    if pred.current_affairs_json and isinstance(pred.current_affairs_json, dict):
        q_count += len(pred.current_affairs_json.get("questions", []))

    return PredictionResponse(
        id=pred.id,
        job_type_id=pred.job_type_id,
        title=pred.title,
        prediction_date=pred.prediction_date,
        total_questions=pred.total_questions,
        include_current_affairs=pred.include_current_affairs,
        questions_json=pred.questions_json,
        current_affairs_json=pred.current_affairs_json,
        topic_distribution=pred.topic_distribution,
        generation_metadata=pred.generation_metadata,
        confidence_score=pred.confidence_score,
        paper_count_basis=pred.paper_count_basis,
        pattern_consistency=pred.pattern_consistency,
        status=pred.status,
        is_published=pred.is_published,
        published_at=pred.published_at,
        snapshot_id=pred.snapshot_id,
        created_at=pred.created_at,
        updated_at=pred.updated_at,
        job_type_name=jt.name if jt else None,
        question_count_generated=q_count,
    )


@router.get(
    "/",
    response_model=PredictionListResponse,
    summary="List published predictions",
)
async def list_predictions(
    db: DBSession,
    current_user=Depends(get_current_user),
    job_type_id: UUID | None = Query(None, description="Filter by job type"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List published predictions available to students."""
    skip = (page - 1) * per_page
    items, total = await crud_prediction.get_published(
        db, job_type_id=job_type_id, skip=skip, limit=per_page,
    )
    return PredictionListResponse(
        items=[_build_response(p) for p in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse,
    summary="Get a published prediction",
)
async def get_prediction(
    prediction_id: UUID,
    db: DBSession,
    current_user=Depends(get_current_user),
):
    """Get a single published prediction."""
    pred = await crud_prediction.get_or_404(db, id=prediction_id)
    if not pred.is_published:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found or not published",
        )
    return _build_response(pred)
