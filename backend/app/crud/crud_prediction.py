"""
CRUD operations for Prediction records.
"""

from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionGenerateRequest, PredictionUpdate


class CRUDPrediction(CRUDBase[Prediction, PredictionGenerateRequest, PredictionUpdate]):
    """Prediction-specific CRUD methods."""

    async def get_by_job_type(
        self,
        db: AsyncSession,
        *,
        job_type_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status_filter: str | None = None,
    ) -> tuple[Sequence[Prediction], int]:
        """List predictions for a specific job type with optional status filter."""
        query = select(self.model).where(self.model.job_type_id == job_type_id)
        count_query = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.job_type_id == job_type_id)
        )

        if status_filter:
            query = query.where(self.model.status == status_filter)
            count_query = count_query.where(self.model.status == status_filter)

        total = (await db.execute(count_query)).scalar() or 0
        query = (
            query.order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all(), total

    async def get_published(
        self,
        db: AsyncSession,
        *,
        job_type_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Prediction], int]:
        """List published predictions."""
        query = select(self.model).where(self.model.is_published.is_(True))
        count_query = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.is_published.is_(True))
        )

        if job_type_id:
            query = query.where(self.model.job_type_id == job_type_id)
            count_query = count_query.where(self.model.job_type_id == job_type_id)

        total = (await db.execute(count_query)).scalar() or 0
        query = (
            query.order_by(self.model.prediction_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all(), total

    async def update_status(
        self, db: AsyncSession, *, id: UUID, status: str
    ) -> Prediction:
        """Quick status update helper."""
        return await self.update(db, id=id, obj_in={"status": status})

    async def append_question(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        question_data: dict[str, Any],
    ) -> Prediction:
        """Append a single generated question to the prediction's questions_json."""
        pred = await self.get_or_404(db, id=id)
        current_questions = pred.questions_json or {"questions": []}
        if isinstance(current_questions, dict):
            questions_list = current_questions.get("questions", [])
        else:
            questions_list = []

        questions_list.append(question_data)
        pred.questions_json = {"questions": questions_list}
        db.add(pred)
        await db.flush()
        await db.refresh(pred)
        return pred

    async def get_latest_published(
        self,
        db: AsyncSession,
        *,
        job_type_id: UUID | None = None,
    ) -> Prediction | None:
        """Return the single most-recently published prediction, optionally filtered by job type."""
        query = (
            select(self.model)
            .where(self.model.is_published.is_(True))
        )
        if job_type_id:
            query = query.where(self.model.job_type_id == job_type_id)

        query = query.order_by(self.model.published_at.desc()).limit(1)
        result = await db.execute(query)
        return result.scalar_one_or_none()


crud_prediction = CRUDPrediction(Prediction)
