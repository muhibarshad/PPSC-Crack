"""
Prediction Engine — Celery Tasks
===================================
Background tasks for generating exam predictions.

Start worker::

    celery -A app.worker.celery_app worker --loglevel=info -Q ai_pipeline --concurrency=2
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from uuid import UUID

from app.worker import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from within Celery's sync worker."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="app.tasks.prediction_engine.generate_prediction",
    bind=True,
    max_retries=1,
    default_retry_delay=60,
    acks_late=True,
    queue="ai_pipeline",
)
def generate_prediction(
    self,
    job_type_id: str,
    prediction_date: str,
    include_current_affairs: bool = True,
    total_questions: int = 100,
) -> dict:
    """Celery task: runs the full Prediction Engine (non-streaming).

    Used when the admin triggers generation without SSE streaming,
    or for scheduled batch prediction generation.

    Parameters are serialized as strings (UUIDs / dates) since Celery uses JSON.
    """
    from app.database import SessionManager
    from app.services.prediction_engine import run_prediction_engine

    logger.info(
        "Starting prediction generation for job_type=%s date=%s (attempt %d)",
        job_type_id, prediction_date, self.request.retries + 1,
    )

    parsed_date = date.fromisoformat(prediction_date)

    async def _execute():
        async with SessionManager() as db:
            return await run_prediction_engine(
                db,
                job_type_id=UUID(job_type_id),
                prediction_date=parsed_date,
                include_current_affairs=include_current_affairs,
                total_questions=total_questions,
            )

    try:
        result = _run_async(_execute())
        logger.info(
            "Prediction generation complete for job_type=%s: %s",
            job_type_id, result.get("status"),
        )
        return result
    except Exception as exc:
        logger.exception(
            "Prediction generation failed for job_type=%s: %s",
            job_type_id, exc,
        )
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.prediction_engine.trigger_prediction_generation",
    bind=True,
    max_retries=0,
    queue="ai_pipeline",
)
def trigger_prediction_generation(
    self,
    job_type_id: str,
    prediction_date: str,
    include_current_affairs: bool = True,
    total_questions: int = 100,
) -> dict:
    """Fire-and-forget wrapper that dispatches the actual generation task.

    Returns immediately with the dispatched task ID.
    """
    task = generate_prediction.delay(
        job_type_id=job_type_id,
        prediction_date=prediction_date,
        include_current_affairs=include_current_affairs,
        total_questions=total_questions,
    )
    logger.info(
        "Dispatched prediction generation task=%s for job_type=%s",
        task.id, job_type_id,
    )
    return {
        "status": "dispatched",
        "task_id": task.id,
        "job_type_id": job_type_id,
        "prediction_date": prediction_date,
    }
