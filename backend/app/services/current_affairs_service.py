"""
Current affairs service.
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.current_affair import CurrentAffair
from app.core.exceptions import NotFound


async def list_articles(
    db: AsyncSession,
    category: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[CurrentAffair], int]:
    """Return current affairs with optional category filter."""
    query = select(CurrentAffair)
    count_query = select(func.count()).select_from(CurrentAffair)

    if category:
        query = query.where(CurrentAffair.category == category)
        count_query = count_query.where(CurrentAffair.category == category)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.offset(skip).limit(limit).order_by(CurrentAffair.published_at.desc())
    )
    return list(result.scalars().all()), total


async def get_article_by_id(db: AsyncSession, article_id: int) -> CurrentAffair:
    """Fetch a single article."""
    result = await db.execute(select(CurrentAffair).where(CurrentAffair.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise NotFound(f"Article {article_id} not found")
    return article
