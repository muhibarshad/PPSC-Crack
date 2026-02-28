"""
Pattern Intelligence Celery Task
==================================
Triggered after each paper ingestion to run the full pattern engine.
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
    name="app.tasks.pattern_engine.run_pattern_analysis",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
    queue="ai_pipeline",
)
def run_pattern_analysis(
    self,
    paper_id: str,
    job_type_id: str,
) -> dict:
    """Celery task: runs the full Pattern Intelligence Engine.

    Triggered after paper ingestion AI pipeline completes.
    Parameters are serialized as strings (UUIDs) since Celery uses JSON.
    """
    from app.database import SessionManager
    from app.services.pattern_engine import run_pattern_engine

    logger.info(
        "Starting pattern analysis for paper=%s job_type=%s (attempt %d)",
        paper_id, job_type_id, self.request.retries + 1,
    )

    async def _execute():
        async with SessionManager() as db:
            return await run_pattern_engine(
                db,
                paper_id=UUID(paper_id),
                job_type_id=UUID(job_type_id),
            )

    try:
        result = _run_async(_execute())
        logger.info(
            "Pattern analysis complete for paper=%s: %s",
            paper_id, result.get("status"),
        )
        return result
    except Exception as exc:
        logger.exception(
            "Pattern analysis failed for paper=%s: %s", paper_id, exc,
        )
        raise self.retry(exc=exc)
