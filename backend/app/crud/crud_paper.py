"""CRUD helpers for **Paper** model."""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.paper import Paper
from app.schemas.paper import PaperCreate, PaperUpdate


class CRUDPaper(CRUDBase[Paper, PaperCreate, PaperUpdate]):
    """Extended CRUD for papers table."""

    async def get_by_job_type(
        self,
        db: AsyncSession,
        *,
        job_type_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Paper], int]:
        """List papers for a specific job type with count."""
        base = select(self.model).where(self.model.job_type_id == job_type_id)
        count_q = select(func.count()).select_from(self.model).where(
            self.model.job_type_id == job_type_id
        )

        total: int = (await db.execute(count_q)).scalar() or 0
        result = await db.execute(
            base.order_by(self.model.paper_year.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all(), total

    async def get_by_year(
        self, db: AsyncSession, *, year: int
    ) -> list[Paper]:
        """Return all papers from a given year."""
        result = await db.execute(
            select(self.model)
            .where(self.model.paper_year == year)
            .order_by(self.model.title.asc())
        )
        return list(result.scalars().all())

    async def get_pending_ingestion(
        self, db: AsyncSession, *, limit: int = 10
    ) -> list[Paper]:
        """Return papers that still need processing."""
        result = await db.execute(
            select(self.model)
            .where(self.model.ingestion_status == "pending")
            .order_by(self.model.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def set_ingestion_status(
        self, db: AsyncSession, *, id: UUID, status: str
    ) -> Paper:
        """Update ingestion status (pending/processing/completed/failed)."""
        return await self.update(db, id=id, obj_in={"ingestion_status": status})

    async def years_available(
        self, db: AsyncSession, *, job_type_id: UUID | None = None
    ) -> list[int]:
        """Return distinct years that have papers, newest first."""
        query = select(self.model.paper_year).distinct()
        if job_type_id:
            query = query.where(self.model.job_type_id == job_type_id)
        query = query.order_by(self.model.paper_year.desc())
        result = await db.execute(query)
        return list(result.scalars().all())


crud_paper = CRUDPaper(Paper)
