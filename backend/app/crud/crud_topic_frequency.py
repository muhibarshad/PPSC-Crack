"""CRUD helpers for **TopicFrequencyByJob** model."""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.topic_frequency import TopicFrequencyByJob
from app.schemas.topic_frequency import TopicFrequencyCreate


class _NoUpdate:
    """Placeholder — topic frequency rows are replaced, not patched."""
    pass


class CRUDTopicFrequency(CRUDBase[TopicFrequencyByJob, TopicFrequencyCreate, _NoUpdate]):
    """Extended CRUD for topic_frequency_by_job table."""

    async def get_by_topic(
        self,
        db: AsyncSession,
        *,
        topic_id: UUID,
        order_by_year: bool = True,
    ) -> Sequence[TopicFrequencyByJob]:
        """All frequency rows for a topic, newest year first."""
        query = select(self.model).where(self.model.topic_id == topic_id)
        if order_by_year:
            query = query.order_by(self.model.year.desc())
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_job_type(
        self,
        db: AsyncSession,
        *,
        job_type_id: UUID,
        year: int | None = None,
    ) -> Sequence[TopicFrequencyByJob]:
        """Frequency rows for a job type, optionally filtered by year."""
        query = select(self.model).where(self.model.job_type_id == job_type_id)
        if year is not None:
            query = query.where(self.model.year == year)
        query = query.order_by(self.model.percentage_of_paper.desc())
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_topic_and_job(
        self,
        db: AsyncSession,
        *,
        topic_id: UUID,
        job_type_id: UUID,
    ) -> Sequence[TopicFrequencyByJob]:
        """Year-by-year frequency for one topic + one job type."""
        result = await db.execute(
            select(self.model)
            .where(self.model.topic_id == topic_id)
            .where(self.model.job_type_id == job_type_id)
            .order_by(self.model.year.desc())
        )
        return result.scalars().all()

    async def upsert(
        self, db: AsyncSession, *, obj_in: TopicFrequencyCreate
    ) -> TopicFrequencyByJob:
        """Insert or update (match by unique constraint)."""
        existing = await db.execute(
            select(self.model)
            .where(self.model.topic_id == obj_in.topic_id)
            .where(self.model.job_type_id == obj_in.job_type_id)
            .where(self.model.year == obj_in.year)
        )
        row = existing.scalar_one_or_none()

        if row:
            row.question_count = obj_in.question_count
            row.percentage_of_paper = obj_in.percentage_of_paper
            db.add(row)
            await db.flush()
            await db.refresh(row)
            return row

        return await self.create(db, obj_in=obj_in)


crud_topic_frequency = CRUDTopicFrequency(TopicFrequencyByJob)
