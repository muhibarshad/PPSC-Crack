"""
Current affairs service — orchestration layer.

Re-exports the daily pipeline components and provides convenience
functions used by the Celery task and API endpoints.
"""

from datetime import date
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.current_affair import CurrentAffairsItem
from app.core.exceptions import NotFound
from app.services.rss_fetcher import fetch_all_feeds, RawArticle
from app.services.ca_relevance_scorer import (
    score_article,
    build_category_frequency_profile,
    RELEVANCE_THRESHOLD,
    CA_CATEGORIES,
)
from app.services.ca_mcq_generator import generate_mcq_for_article


async def list_articles(
    db: AsyncSession,
    category: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[CurrentAffairsItem], int]:
    """Return current affairs with optional category filter."""
    query = select(CurrentAffairsItem)
    count_query = select(func.count()).select_from(CurrentAffairsItem)

    if category:
        query = query.where(CurrentAffairsItem.category == category)
        count_query = count_query.where(CurrentAffairsItem.category == category)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.offset(skip).limit(limit).order_by(CurrentAffairsItem.published_date.desc().nullslast())
    )
    return list(result.scalars().all()), total


async def get_article_by_id(db: AsyncSession, article_id: Any) -> CurrentAffairsItem:
    """Fetch a single article."""
    result = await db.execute(
        select(CurrentAffairsItem).where(CurrentAffairsItem.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise NotFound(f"Article {article_id} not found")
    return article


async def get_category_distribution(db: AsyncSession) -> dict[str, int]:
    """Return count of articles per category."""
    result = await db.execute(
        select(
            CurrentAffairsItem.category,
            func.count(CurrentAffairsItem.id),
        )
        .group_by(CurrentAffairsItem.category)
    )
    return {row[0]: row[1] for row in result.fetchall()}
