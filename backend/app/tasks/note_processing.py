"""
Admin Note Processing — Celery Tasks
=======================================
Background tasks for processing admin-contributed notes through the
AI pipeline (topic identification → fact extraction → embedding →
incremental story update).

Start worker::

    celery -A app.worker.celery_app worker --loglevel=info -Q ai_pipeline --concurrency=2
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


# ═════════════════════════════════════════════════════════════
# Single note processing
# ═════════════════════════════════════════════════════════════

@celery_app.task(
    name="app.tasks.note_processing.process_admin_note",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
    queue="ai_pipeline",
)
def process_admin_note(self, note_id: str) -> dict:
    """Process a single admin note through the AI pipeline.

    Pipeline steps:
    1. GPT-4o identifies topic + extracts facts + determines story section.
    2. Generates embedding (text-embedding-3-small, 1536 dims).
    3. Stores processed_content, assigned_topic_id, position_in_story, embedding.
    4. Queues incremental story update for the assigned topic.
    5. Marks note as processed=True.

    Parameters
    ----------
    note_id : str
        UUID of the AdminNote (JSON-serialized).

    Returns
    -------
    dict
        Processing result summary.
    """
    from app.database import SessionManager
    from app.services.note_processor import run_note_processing

    logger.info(
        "Admin note processing started for note=%s (attempt %d)",
        note_id, self.request.retries + 1,
    )

    async def _execute():
        async with SessionManager() as db:
            return await run_note_processing(db, note_id=UUID(note_id))

    try:
        result = _run_async(_execute())
        logger.info(
            "Admin note processing complete for note=%s: status=%s, topic=%s, facts=%d",
            note_id,
            result.get("status"),
            result.get("topic_name", "N/A"),
            result.get("facts_count", 0),
        )
        return result
    except Exception as exc:
        logger.exception("Admin note processing failed for note=%s: %s", note_id, exc)
        raise self.retry(exc=exc)


# ═════════════════════════════════════════════════════════════
# Batch processing (all unprocessed notes)
# ═════════════════════════════════════════════════════════════

@celery_app.task(
    name="app.tasks.note_processing.batch_process_admin_notes",
    bind=True,
    max_retries=1,
    default_retry_delay=120,
    acks_late=True,
    queue="ai_pipeline",
    soft_time_limit=1800,
    time_limit=2400,
)
def batch_process_admin_notes(self, limit: int = 50) -> dict:
    """Process all unprocessed admin notes (up to *limit*).

    Returns
    -------
    dict
        Summary with counts and per-note results.
    """
    from app.database import SessionManager
    from app.services.note_processor import run_batch_note_processing

    logger.info(
        "Batch admin note processing started (limit=%d, attempt %d)",
        limit, self.request.retries + 1,
    )

    async def _execute():
        async with SessionManager() as db:
            return await run_batch_note_processing(db, limit=limit)

    try:
        results = _run_async(_execute())
        processed = sum(1 for r in results if r.get("status") == "processed")
        errors = sum(1 for r in results if r.get("status") == "error")
        logger.info(
            "Batch admin note processing complete: %d processed, %d errors, %d total",
            processed, errors, len(results),
        )
        return {
            "status": "complete",
            "total_processed": len(results),
            "processed": processed,
            "errors": errors,
            "results": results,
        }
    except Exception as exc:
        logger.exception("Batch admin note processing failed: %s", exc)
        raise self.retry(exc=exc)


# ═════════════════════════════════════════════════════════════
# Fire-and-forget trigger
# ═════════════════════════════════════════════════════════════

def trigger_note_processing(note_id: str) -> str:
    """Enqueue processing for a single admin note.

    Returns the Celery task ID.
    """
    task = process_admin_note.apply_async(
        args=[note_id],
        queue="ai_pipeline",
    )
    logger.info("Enqueued admin note processing for note=%s (task=%s)", note_id, task.id)
    return task.id
