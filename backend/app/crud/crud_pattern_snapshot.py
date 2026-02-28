"""CRUD helpers for **PatternSnapshot** model."""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.pattern_snapshot import PatternSnapshot
from app.schemas.pattern_snapshot import PatternSnapshotCreate


class _NoUpdate:
    """Snapshots are immutable — no update schema."""
    pass


class CRUDPatternSnapshot(CRUDBase[PatternSnapshot, PatternSnapshotCreate, _NoUpdate]):
    """Extended CRUD for pattern_snapshots table."""

    async def get_latest_by_job(
        self, db: AsyncSession, *, job_type_id: UUID
    ) -> PatternSnapshot | None:
        """Return the most recent snapshot for a job type."""
        result = await db.execute(
            select(self.model)
            .where(self.model.job_type_id == job_type_id)
            .order_by(self.model.snapshot_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(
        self,
        db: AsyncSession,
        *,
        job_type_id: UUID,
        limit: int = 10,
    ) -> Sequence[PatternSnapshot]:
        """Return snapshot history for a job type, newest first."""
        result = await db.execute(
            select(self.model)
            .where(self.model.job_type_id == job_type_id)
            .order_by(self.model.snapshot_date.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_high_confidence(
        self,
        db: AsyncSession,
        *,
        min_confidence: float = 0.8,
        limit: int = 20,
    ) -> Sequence[PatternSnapshot]:
        """Return snapshots above a confidence threshold."""
        result = await db.execute(
            select(self.model)
            .where(self.model.confidence_score >= min_confidence)
            .order_by(self.model.confidence_score.desc())
            .limit(limit)
        )
        return result.scalars().all()


crud_pattern_snapshot = CRUDPatternSnapshot(PatternSnapshot)
