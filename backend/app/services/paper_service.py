"""
Paper service — past paper CRUD.
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper
from app.core.exceptions import NotFound


async def list_papers(
    db: AsyncSession,
    job_type: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Paper], int]:
    """Return papers with optional job-type filter + total count."""
    query = select(Paper)
    count_query = select(func.count()).select_from(Paper)

    if job_type:
        query = query.where(Paper.job_type == job_type)
        count_query = count_query.where(Paper.job_type == job_type)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.offset(skip).limit(limit).order_by(Paper.year.desc()))
    return list(result.scalars().all()), total


async def get_paper_by_id(db: AsyncSession, paper_id: int) -> Paper:
    """Fetch a single paper."""
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise NotFound(f"Paper {paper_id} not found")
    return paper
