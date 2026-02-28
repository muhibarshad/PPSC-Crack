"""
Paper Ingestion Celery Tasks
==============================
Background tasks for AI-powered paper processing (steps 4-8).
"""

from __future__ import annotations

import asyncio
import logging
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
    name="app.tasks.paper_ingestion.run_ai_pipeline",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
    queue="ai_pipeline",
)
def run_ai_pipeline(
    self,
    paper_id: str,
    job_type_id: str,
    paper_year: int,
) -> dict:
    """Celery task: runs AI steps 4-8 for a paper.

    Parameters are serialized as strings (UUIDs) since Celery uses JSON.
    """
    from app.database import SessionManager
    from app.services.paper_ingestion.pipeline import run_ai_steps

    logger.info(
        "Starting AI pipeline task for paper=%s (attempt %d)",
        paper_id, self.request.retries + 1,
    )

    async def _execute():
        async with SessionManager() as db:
            return await run_ai_steps(
                db,
                paper_id=UUID(paper_id),
                job_type_id=UUID(job_type_id),
                paper_year=paper_year,
            )

    try:
        result = _run_async(_execute())
        logger.info("AI pipeline task complete for paper=%s: %s", paper_id, result.get("status"))

        # ── Trigger Pattern Intelligence Engine ──────────────
        from app.tasks.pattern_engine import run_pattern_analysis
        run_pattern_analysis.apply_async(
            args=[paper_id, job_type_id],
            countdown=5,  # short delay to let DB writes settle
        )
        logger.info("Pattern analysis queued for paper=%s", paper_id)

        return result
    except Exception as exc:
        logger.exception("AI pipeline task failed for paper=%s: %s", paper_id, exc)
        # Retry on transient failures
        raise self.retry(exc=exc)
