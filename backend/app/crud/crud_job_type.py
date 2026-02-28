"""CRUD helpers for **JobType** model."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.job_type import JobType
from app.schemas.job_type import JobTypeCreate, JobTypeUpdate


class CRUDJobType(CRUDBase[JobType, JobTypeCreate, JobTypeUpdate]):
    """Extended CRUD for job_types table."""

    async def get_by_slug(self, db: AsyncSession, *, slug: str) -> JobType | None:
        """Look up a job type by its URL-safe slug."""
        result = await db.execute(select(self.model).where(self.model.slug == slug))
        return result.scalar_one_or_none()

    async def get_active(self, db: AsyncSession) -> list[JobType]:
        """Return only active job types."""
        result = await db.execute(
            select(self.model)
            .where(self.model.is_active.is_(True))
            .order_by(self.model.name.asc())
        )
        return list(result.scalars().all())

    async def update_topic_ratios(
        self, db: AsyncSession, *, id: UUID, ratios: dict
    ) -> JobType:
        """Update the pre-computed topic ratio JSON."""
        from datetime import datetime, timezone

        return await self.update(
            db,
            id=id,
            obj_in={
                "topic_ratios": ratios,
                "last_updated_ratios": datetime.now(timezone.utc),
            },
        )

    async def increment_paper_count(
        self, db: AsyncSession, *, id: UUID
    ) -> JobType:
        """Atomically increment total_papers by 1."""
        obj = await self.get_or_404(db, id=id)
        obj.total_papers = (obj.total_papers or 0) + 1
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj


crud_job_type = CRUDJobType(JobType)
