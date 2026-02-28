"""
Story Document Generation — Celery Task
==========================================
Background task that generates (or regenerates) the AI-powered
narrative story document for a topic.

Trigger conditions:
  - Automatically when a topic reaches 10+ questions.
  - Manually via the admin API endpoint.
  - Batch mode to back-fill all eligible topics.

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
# Single-topic story generation
# ═════════════════════════════════════════════════════════════

@celery_app.task(
    name="app.tasks.story_generation.generate_story_document",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
    queue="ai_pipeline",
)
def generate_story_document(
    self,
    topic_id: str,
    force: bool = False,
) -> dict:
    """Celery task: generate the story document for a single topic.

    Parameters
    ----------
    topic_id : str
        UUID of the topic (serialized as string for JSON transport).
    force : bool
        If True, regenerate even if below threshold or story already exists.

    Returns
    -------
    dict
        Result summary from the StoryEngine.
    """
    from app.database import SessionManager
    from app.services.story_engine import run_story_generation

    logger.info(
        "Story generation task started for topic=%s force=%s (attempt %d)",
        topic_id, force, self.request.retries + 1,
    )

    async def _execute():
        async with SessionManager() as db:
            return await run_story_generation(
                db,
                topic_id=UUID(topic_id),
                force=force,
            )

    try:
        result = _run_async(_execute())
        logger.info(
            "Story generation complete for topic=%s: status=%s, words=%s",
            topic_id,
            result.get("status"),
            result.get("word_count", "N/A"),
        )
        return result
    except Exception as exc:
        logger.exception(
            "Story generation failed for topic=%s: %s", topic_id, exc,
        )
        raise self.retry(exc=exc)


# ═════════════════════════════════════════════════════════════
# Batch story generation (all eligible topics)
# ═════════════════════════════════════════════════════════════

@celery_app.task(
    name="app.tasks.story_generation.batch_generate_stories",
    bind=True,
    max_retries=1,
    default_retry_delay=120,
    acks_late=True,
    queue="ai_pipeline",
    soft_time_limit=1800,   # 30 min soft limit for batch
    time_limit=2400,        # 40 min hard limit
)
def batch_generate_stories(self) -> dict:
    """Celery task: scan all topics and generate stories for those with 10+ questions.

    Returns
    -------
    dict
        Summary with counts and per-topic results.
    """
    from app.database import SessionManager
    from app.services.story_engine import run_batch_story_generation

    logger.info("Batch story generation task started (attempt %d)", self.request.retries + 1)

    async def _execute():
        async with SessionManager() as db:
            return await run_batch_story_generation(db)

    try:
        results = _run_async(_execute())
        generated = sum(1 for r in results if r.get("status") == "generated")
        errors = sum(1 for r in results if r.get("status") == "error")
        logger.info(
            "Batch story generation complete: %d generated, %d errors, %d total",
            generated, errors, len(results),
        )
        return {
            "status": "complete",
            "total_processed": len(results),
            "generated": generated,
            "errors": errors,
            "results": results,
        }
    except Exception as exc:
        logger.exception("Batch story generation failed: %s", exc)
        raise self.retry(exc=exc)


# ═════════════════════════════════════════════════════════════
# Auto-trigger helper (call from paper ingestion pipeline)
# ═════════════════════════════════════════════════════════════

def trigger_story_if_eligible(topic_id: str) -> None:
    """Fire-and-forget: enqueue story generation for a topic.

    Designed to be called at the end of the paper ingestion pipeline
    for each topic that received new questions. The task itself checks
    whether the topic has reached the 10-question threshold.
    """
    generate_story_document.apply_async(
        args=[topic_id],
        kwargs={"force": False},
        queue="ai_pipeline",
    )
    logger.info("Enqueued story generation check for topic=%s", topic_id)


# ═════════════════════════════════════════════════════════════
# Incremental story update (after paper ingestion)
# ═════════════════════════════════════════════════════════════

@celery_app.task(
    name="app.tasks.story_generation.incremental_story_update",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
    queue="ai_pipeline",
)
def incremental_story_update(
    self,
    topic_id: str,
    paper_id: str,
) -> dict:
    """Celery task: incrementally update a topic's story document with
    new facts extracted from a specific paper.

    This task **never regenerates the full document**.  It:
      1. Collects new facts from the paper for the topic.
      2. Embeds new facts + existing story sections.
      3. Routes each fact to the best-matching section via cosine similarity.
      4. Calls GPT-4o once per affected section to surgically incorporate facts.
      5. Replaces only the changed sections and persists the result.

    If the topic does not yet have a story document, this task returns
    a ``no_story`` status so the caller can fall back to full generation.

    Parameters
    ----------
    topic_id : str
        UUID of the topic (JSON-serialized).
    paper_id : str
        UUID of the paper whose new facts to incorporate.

    Returns
    -------
    dict
        Result summary from IncrementalStoryEngine.
    """
    from app.database import SessionManager
    from app.services.story_incremental import run_incremental_story_update

    logger.info(
        "Incremental story update started for topic=%s paper=%s (attempt %d)",
        topic_id, paper_id, self.request.retries + 1,
    )

    async def _execute():
        async with SessionManager() as db:
            return await run_incremental_story_update(
                db,
                topic_id=UUID(topic_id),
                paper_id=UUID(paper_id),
            )

    try:
        result = _run_async(_execute())
        logger.info(
            "Incremental story update complete for topic=%s paper=%s: "
            "status=%s, sections_updated=%s",
            topic_id, paper_id,
            result.get("status"),
            result.get("sections_updated", []),
        )
        return result
    except Exception as exc:
        logger.exception(
            "Incremental story update failed for topic=%s paper=%s: %s",
            topic_id, paper_id, exc,
        )
        raise self.retry(exc=exc)


def trigger_incremental_story_update(topic_id: str, paper_id: str) -> None:
    """Fire-and-forget: enqueue an incremental story update.

    Call this at the end of the paper ingestion pipeline for each
    affected topic that already has a story document.  The task itself
    checks whether a story exists and gracefully returns ``no_story``
    if one doesn't.

    For topics that don't have a story yet, use
    :func:`trigger_story_if_eligible` instead (or let the orchestrator
    decide based on question count).
    """
    incremental_story_update.apply_async(
        args=[topic_id, paper_id],
        queue="ai_pipeline",
    )
    logger.info(
        "Enqueued incremental story update for topic=%s paper=%s",
        topic_id, paper_id,
    )


def trigger_story_update_smart(topic_id: str, paper_id: str) -> None:
    """Smart trigger: decides between incremental update and full generation.

    - If the topic already has a story → enqueue incremental update.
    - If not → enqueue full generation (which checks the 10-question threshold).

    This is the **recommended** single entry-point to call from the paper
    ingestion pipeline.
    """
    # Defer the DB check to the tasks themselves — just enqueue both;
    # the incremental task will no-op if there's no story, and the
    # generation task will no-op if a story already exists and force=False.
    incremental_story_update.apply_async(
        args=[topic_id, paper_id],
        queue="ai_pipeline",
    )
    logger.info(
        "Enqueued smart story update for topic=%s paper=%s",
        topic_id, paper_id,
    )


# ═════════════════════════════════════════════════════════════
# Incremental story update from explicit fact list
# ═════════════════════════════════════════════════════════════

@celery_app.task(
    name="app.tasks.story_generation.incremental_facts_update",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
    queue="ai_pipeline",
)
def incremental_facts_update(
    self,
    topic_id: str,
    fact_texts: list[str] | None = None,
) -> dict:
    """Celery task: incrementally update a topic's story document with
    an explicit list of fact strings (not tied to a specific paper).

    Parameters
    ----------
    topic_id : str
        UUID of the topic (JSON-serialized).
    fact_texts : list[str]
        The facts to incorporate.

    Returns
    -------
    dict
        Result summary from IncrementalStoryEngine.
    """
    from app.database import SessionManager
    from app.services.story_incremental import run_incremental_story_update_from_facts

    facts = fact_texts or []
    logger.info(
        "Incremental facts update started for topic=%s with %d facts (attempt %d)",
        topic_id, len(facts), self.request.retries + 1,
    )

    async def _execute():
        async with SessionManager() as db:
            return await run_incremental_story_update_from_facts(
                db,
                topic_id=UUID(topic_id),
                fact_texts=facts,
            )

    try:
        result = _run_async(_execute())
        logger.info(
            "Incremental facts update complete for topic=%s: status=%s",
            topic_id, result.get("status"),
        )
        return result
    except Exception as exc:
        logger.exception(
            "Incremental facts update failed for topic=%s: %s", topic_id, exc,
        )
        raise self.retry(exc=exc)
