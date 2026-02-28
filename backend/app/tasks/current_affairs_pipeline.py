"""
Current Affairs Daily Pipeline — Celery Task
===============================================
Scheduled via Celery Beat at 6:00 AM PKT (01:00 UTC) every day.

Pipeline steps:
  1. Fetch RSS feeds (dawn.com, geo.tv, app.com.pk)
  2. De-duplicate against existing source_urls in DB
  3. Compute embeddings for new articles
  4. Score relevance (keyword + semantic + recency + category)
  5. Store articles with relevance_score > 0.65
  6. Generate MCQs for top 10 daily articles via GPT-4o
  7. Log summary
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone
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


async def _execute_daily_pipeline() -> dict:
    """Full async pipeline execution."""
    from sqlalchemy import select

    from app.database import SessionManager
    from app.models.current_affair import CurrentAffairsItem
    from app.services.rss_fetcher import fetch_all_feeds, RawArticle
    from app.services.ca_relevance_scorer import (
        score_article,
        build_category_frequency_profile,
        RELEVANCE_THRESHOLD,
    )
    from app.services.ca_mcq_generator import generate_mcqs_for_top_articles
    from app.services.openai.client import get_openai_service

    stats = {
        "articles_fetched": 0,
        "articles_new": 0,
        "articles_stored": 0,
        "mcqs_generated": 0,
        "errors": [],
    }

    # ── Step 1: Fetch RSS feeds ──────────────────────────────
    logger.info("Step 1: Fetching RSS feeds...")
    raw_articles = await fetch_all_feeds()
    stats["articles_fetched"] = len(raw_articles)

    if not raw_articles:
        logger.warning("No articles fetched from any feed. Aborting.")
        return stats

    # ── Step 2: De-duplicate against DB ──────────────────────
    logger.info("Step 2: De-duplicating %d articles...", len(raw_articles))

    async with SessionManager() as db:
        existing_urls_result = await db.execute(
            select(CurrentAffairsItem.source_url).where(
                CurrentAffairsItem.source_url.isnot(None)
            )
        )
        existing_urls: set[str] = {
            row[0] for row in existing_urls_result.fetchall() if row[0]
        }

    new_articles = [
        a for a in raw_articles
        if a.source_url and a.source_url not in existing_urls
    ]
    stats["articles_new"] = len(new_articles)
    logger.info("Found %d new articles (skipped %d duplicates)",
                len(new_articles), len(raw_articles) - len(new_articles))

    if not new_articles:
        logger.info("No new articles to process.")
        return stats

    # ── Step 3: Compute embeddings ───────────────────────────
    logger.info("Step 3: Computing embeddings for %d articles...", len(new_articles))
    openai_svc = get_openai_service()

    # Batch embed headline + summary for efficiency
    embed_texts = [
        f"{a.headline}. {a.summary[:500]}" for a in new_articles
    ]

    embeddings: list[list[float]] = []
    try:
        # Process in batches of 20 to stay within rate limits
        batch_size = 20
        for i in range(0, len(embed_texts), batch_size):
            batch = embed_texts[i : i + batch_size]
            batch_embeddings = await openai_svc.embed(batch)
            embeddings.extend(batch_embeddings)
    except Exception as exc:
        logger.error("Embedding generation failed: %s", exc)
        stats["errors"].append(f"Embedding error: {exc}")
        # Continue with empty embeddings — keyword/recency/category still work
        embeddings = [[] for _ in new_articles]

    # ── Step 4: Build category profile & score articles ──────
    logger.info("Step 4: Scoring %d articles...", len(new_articles))

    async with SessionManager() as db:
        category_profile = await build_category_frequency_profile(db)

        scored_articles: list[tuple[RawArticle, dict, list[float]]] = []

        for article, embedding in zip(new_articles, embeddings):
            try:
                result = await score_article(
                    db, article, category_profile, embedding or None
                )

                if result.composite_score >= RELEVANCE_THRESHOLD:
                    scored_articles.append((
                        article,
                        {
                            "keyword_score": result.keyword_score,
                            "semantic_score": result.semantic_score,
                            "recency_score": result.recency_score,
                            "category_score": result.category_score,
                            "relevance_score": result.composite_score,
                            "category": result.matched_category,
                        },
                        embedding,
                    ))
            except Exception as exc:
                logger.error("Scoring failed for '%s': %s", article.headline[:60], exc)
                stats["errors"].append(f"Score error: {article.headline[:40]}")

        logger.info(
            "%d articles passed relevance threshold (%.2f)",
            len(scored_articles), RELEVANCE_THRESHOLD,
        )

    # ── Step 5: Store qualifying articles ────────────────────
    logger.info("Step 5: Storing %d articles...", len(scored_articles))

    stored_items: list[CurrentAffairsItem] = []

    async with SessionManager() as db:
        for article, scores, embedding in scored_articles:
            try:
                item = CurrentAffairsItem(
                    headline=article.headline,
                    summary=article.summary,
                    content=article.content,
                    category=scores["category"],
                    source_name=article.source_name,
                    source_url=article.source_url,
                    published_date=article.published_date,
                    relevance_score=scores["relevance_score"],
                    keyword_score=scores["keyword_score"],
                    semantic_score=scores["semantic_score"],
                    recency_score=scores["recency_score"],
                    category_score=scores["category_score"],
                    embedding=embedding if embedding else None,
                )
                db.add(item)
                stored_items.append(item)
            except Exception as exc:
                logger.error("Failed to store article '%s': %s", article.headline[:60], exc)
                stats["errors"].append(f"Store error: {article.headline[:40]}")

        await db.flush()

        # Refresh to get DB-generated IDs
        for item in stored_items:
            await db.refresh(item)

        stats["articles_stored"] = len(stored_items)
        logger.info("Stored %d articles successfully", len(stored_items))

        # ── Step 6: Generate MCQs for top 10 ────────────────
        logger.info("Step 6: Generating MCQs for top 10 articles...")

        try:
            mcq_results = await generate_mcqs_for_top_articles(
                stored_items,
                max_count=10,
                openai_svc=openai_svc,
            )

            for item, mcq_data in mcq_results:
                item.mcq_generated = True
                item.mcq_text = mcq_data["mcq_text"]
                item.mcq_options = mcq_data["mcq_options"]
                item.mcq_correct_answer = mcq_data["mcq_correct_answer"]
                item.mcq_explanation = mcq_data["mcq_explanation"]
                db.add(item)

            stats["mcqs_generated"] = len(mcq_results)
            logger.info("Generated %d MCQs", len(mcq_results))

        except Exception as exc:
            logger.exception("MCQ generation failed: %s", exc)
            stats["errors"].append(f"MCQ error: {exc}")

    # ── Summary ──────────────────────────────────────────────
    logger.info(
        "Daily CA pipeline complete: fetched=%d, new=%d, stored=%d, mcqs=%d, errors=%d",
        stats["articles_fetched"],
        stats["articles_new"],
        stats["articles_stored"],
        stats["mcqs_generated"],
        len(stats["errors"]),
    )

    return stats


@celery_app.task(
    name="app.tasks.current_affairs_pipeline.run_daily_current_affairs",
    bind=True,
    max_retries=2,
    default_retry_delay=300,  # 5 min between retries
    acks_late=True,
    queue="default",
)
def run_daily_current_affairs(self) -> dict:
    """Celery task: fetch RSS feeds, score, store, and generate MCQs.

    Scheduled by Celery Beat at 6:00 AM PKT (01:00 UTC) daily.
    """
    logger.info(
        "Starting daily current affairs pipeline (attempt %d)",
        self.request.retries + 1,
    )

    try:
        result = _run_async(_execute_daily_pipeline())
        return result
    except Exception as exc:
        logger.exception("Daily CA pipeline failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.current_affairs_pipeline.run_manual_refresh",
    bind=True,
    max_retries=1,
    acks_late=True,
    queue="default",
)
def run_manual_refresh(self) -> dict:
    """Admin-triggered manual refresh of current affairs feeds."""
    logger.info("Manual current affairs refresh triggered")
    try:
        return _run_async(_execute_daily_pipeline())
    except Exception as exc:
        logger.exception("Manual CA refresh failed: %s", exc)
        raise self.retry(exc=exc)
