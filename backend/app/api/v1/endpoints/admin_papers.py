"""
Admin Paper Ingestion Endpoints
=================================
POST /api/v1/admin/papers          — ingest a new paper (text-paste mode)
GET  /api/v1/admin/papers/{id}/status — poll ingestion progress
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import DBSession, require_admin
from app.schemas.paper_ingestion import (
    PaperIngestRequest,
    PaperIngestResponse,
    ParseSummary,
    IngestionStatusResponse,
)
from app.services.paper_ingestion.pipeline import run_sync_steps
from app.tasks.paper_ingestion import run_ai_pipeline
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/papers",
    response_model=PaperIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a new paper (text-paste mode)",
    description=(
        "Admin pastes 100 MCQs + answer key. Steps 1-3 (parse, map, persist) "
        "run synchronously. Steps 4-8 (classify, extract facts, embed, "
        "similarity check, pattern update) run as a Celery background task."
    ),
)
async def ingest_paper(
    body: PaperIngestRequest,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Ingest a past paper from pasted text."""
    paper_id = uuid.uuid4()

    # ── Steps 1-3: synchronous parse + persist ───────────────
    try:
        sync_summary = await run_sync_steps(
            db,
            paper_id=paper_id,
            job_type_id=body.job_type_id,
            paper_year=body.paper_year,
            paper_month=body.paper_month,
            title=body.title,
            questions_text=body.questions_text,
            answer_key_text=body.answer_key_text,
        )
    except Exception as exc:
        logger.exception("Sync ingestion failed for paper %s: %s", paper_id, exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse paper: {exc}",
        )

    # ── Steps 4-8: dispatch Celery background task ───────────
    task = run_ai_pipeline.delay(
        paper_id=str(paper_id),
        job_type_id=str(body.job_type_id),
        paper_year=body.paper_year,
    )

    logger.info(
        "Paper %s ingestion started by admin=%s. Task=%s",
        paper_id, admin.id, task.id,
    )

    return PaperIngestResponse(
        paper_id=paper_id,
        ingestion_status="processing",
        task_id=task.id,
        parse_summary=ParseSummary(
            total_parsed=sync_summary["total_parsed"],
            total_mapped=sync_summary["total_mapped"],
            unmapped_questions=sync_summary["unmapped_questions"],
            unmapped_answers=sync_summary["unmapped_answers"],
            warnings=sync_summary["warnings"],
        ),
        sync_processing_time_ms=sync_summary["sync_processing_time_ms"],
    )


@router.get(
    "/papers/{paper_id}/status",
    response_model=IngestionStatusResponse,
    summary="Poll paper ingestion status",
)
async def get_ingestion_status(
    paper_id: uuid.UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Check the status of a paper ingestion (sync + background AI pipeline)."""
    from app.models.paper import Paper
    from app.worker import celery_app

    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper {paper_id} not found",
        )

    response = IngestionStatusResponse(
        paper_id=paper_id,
        ingestion_status=paper.ingestion_status,
    )

    # Try to get task status from Celery result backend
    # The admin frontend can poll this endpoint until status is completed/failed
    # We look up task by iterating recent tasks — or the client passes task_id
    return response


@router.get(
    "/papers/{paper_id}/status/{task_id}",
    response_model=IngestionStatusResponse,
    summary="Poll paper ingestion status with task ID",
)
async def get_ingestion_status_with_task(
    paper_id: uuid.UUID,
    task_id: str,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Check the status of a paper ingestion using the Celery task ID."""
    from app.models.paper import Paper
    from app.worker import celery_app

    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper {paper_id} not found",
        )

    # Get Celery task result
    result = celery_app.AsyncResult(task_id)

    response = IngestionStatusResponse(
        paper_id=paper_id,
        ingestion_status=paper.ingestion_status,
        task_id=task_id,
        task_state=result.state,
    )

    if result.ready():
        try:
            response.ai_summary = result.result
        except Exception:
            response.ai_summary = {"error": "Failed to retrieve task result"}

    return response
