"""
Admin Predictions Endpoints
===============================
POST   /api/v1/admin/predictions/generate   — SSE streaming prediction generation
GET    /api/v1/admin/predictions             — list predictions
GET    /api/v1/admin/predictions/{id}        — get single prediction
PUT    /api/v1/admin/predictions/{id}        — update prediction
DELETE /api/v1/admin/predictions/{id}        — delete prediction
POST   /api/v1/admin/predictions/{id}/publish — publish prediction
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DBSession, OpenAI, require_admin
from app.crud.crud_prediction import crud_prediction
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.prediction import (
    PredictionGenerateRequest,
    PredictionListResponse,
    PredictionPublishResponse,
    PredictionResponse,
    PredictionUpdate,
)
from app.services.prediction_engine import PredictionEngine

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────

def _build_response(pred: Prediction) -> PredictionResponse:
    """Map Prediction ORM → PredictionResponse with enriched fields."""
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


# ═════════════════════════════════════════════════════════════
# POST /predictions/generate — SSE streaming endpoint
# ═════════════════════════════════════════════════════════════

@router.post(
    "/predictions/generate",
    summary="Generate AI-powered exam prediction (SSE streaming)",
    description=(
        "Streams the prediction generation process as Server-Sent Events. "
        "Each question is streamed as it's generated. Final event contains "
        "the prediction ID and confidence score."
    ),
)
async def generate_prediction_sse(
    payload: PredictionGenerateRequest,
    db: DBSession,
    openai: OpenAI,
    admin: User = Depends(require_admin),
):
    """SSE streaming prediction generation endpoint.

    Streams events:
    - `status`: progress updates
    - `question`: each generated MCQ
    - `current_affair`: each current affairs MCQ
    - `confidence`: scoring result
    - `complete`: final summary with prediction_id
    - `error`: on failure
    """
    engine = PredictionEngine(db, openai)

    async def event_generator():
        try:
            async for event in engine.generate_streaming(
                job_type_id=payload.job_type_id,
                prediction_date=payload.prediction_date,
                include_current_affairs=payload.include_current_affairs,
                total_questions=payload.total_questions,
            ):
                event_type = event.get("event", "message")
                data = json.dumps(event.get("data", {}), default=str)
                yield f"event: {event_type}\ndata: {data}\n\n"

            # Commit after all events are generated
            await db.commit()
        except Exception as exc:
            logger.exception("SSE prediction generation error: %s", exc)
            error_data = json.dumps({"message": f"Generation failed: {exc}"})
            yield f"event: error\ndata: {error_data}\n\n"
            await db.rollback()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ═════════════════════════════════════════════════════════════
# GET /predictions — list predictions
# ═════════════════════════════════════════════════════════════

@router.get(
    "/predictions",
    response_model=PredictionListResponse,
    summary="List predictions",
)
async def list_predictions(
    db: DBSession,
    admin: User = Depends(require_admin),
    job_type_id: UUID | None = Query(None, description="Filter by job type"),
    status_filter: str | None = Query(
        None, alias="status", description="Filter by status: generating|completed|failed|published"
    ),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List all predictions with optional filtering."""
    skip = (page - 1) * per_page

    if job_type_id:
        items, total = await crud_prediction.get_by_job_type(
            db,
            job_type_id=job_type_id,
            skip=skip,
            limit=per_page,
            status_filter=status_filter,
        )
    else:
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        items, total = await crud_prediction.get_multi(
            db, skip=skip, limit=per_page, filters=filters if filters else None,
        )

    return PredictionListResponse(
        items=[_build_response(p) for p in items],
        total=total,
        page=page,
        per_page=per_page,
    )


# ═════════════════════════════════════════════════════════════
# GET /predictions/{id} — single prediction detail
# ═════════════════════════════════════════════════════════════

@router.get(
    "/predictions/{prediction_id}",
    response_model=PredictionResponse,
    summary="Get prediction detail",
)
async def get_prediction(
    prediction_id: UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Get a single prediction by ID."""
    pred = await crud_prediction.get_or_404(db, id=prediction_id)
    return _build_response(pred)


# ═════════════════════════════════════════════════════════════
# PUT /predictions/{id} — update prediction
# ═════════════════════════════════════════════════════════════

@router.put(
    "/predictions/{prediction_id}",
    response_model=PredictionResponse,
    summary="Update prediction",
)
async def update_prediction(
    prediction_id: UUID,
    payload: PredictionUpdate,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Update a prediction (title, date, questions, etc.)."""
    pred = await crud_prediction.get_or_404(db, id=prediction_id)

    if pred.is_published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit a published prediction. Unpublish it first.",
        )

    updated = await crud_prediction.update(db, id=prediction_id, obj_in=payload)
    await db.commit()
    await db.refresh(updated)
    return _build_response(updated)


# ═════════════════════════════════════════════════════════════
# DELETE /predictions/{id} — delete prediction
# ═════════════════════════════════════════════════════════════

@router.delete(
    "/predictions/{prediction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete prediction",
)
async def delete_prediction(
    prediction_id: UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Delete a prediction by ID."""
    pred = await crud_prediction.get_or_404(db, id=prediction_id)

    if pred.is_published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a published prediction. Unpublish it first.",
        )

    await crud_prediction.delete(db, id=prediction_id)
    await db.commit()
    return None


# ═════════════════════════════════════════════════════════════
# POST /predictions/{id}/publish — publish prediction
# ═════════════════════════════════════════════════════════════

@router.post(
    "/predictions/{prediction_id}/publish",
    response_model=PredictionPublishResponse,
    summary="Publish / unpublish a prediction",
)
async def publish_prediction(
    prediction_id: UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
    action: str = Query("publish", description="publish | unpublish"),
):
    """Publish or unpublish a prediction.

    Published predictions become visible to students.
    """
    pred = await crud_prediction.get_or_404(db, id=prediction_id)

    if pred.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot publish a prediction with status '{pred.status}'. Only completed predictions can be published.",
        )

    if action == "publish":
        pred.is_published = True
        pred.published_at = datetime.now(timezone.utc)
        pred.status = "published"
        message = "Prediction published successfully"
    elif action == "unpublish":
        pred.is_published = False
        pred.published_at = None
        pred.status = "completed"
        message = "Prediction unpublished successfully"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="action must be 'publish' or 'unpublish'",
        )

    self_db = db
    self_db.add(pred)
    await self_db.commit()
    await self_db.refresh(pred)

    return PredictionPublishResponse(
        id=pred.id,
        is_published=pred.is_published,
        published_at=pred.published_at,
        message=message,
    )
