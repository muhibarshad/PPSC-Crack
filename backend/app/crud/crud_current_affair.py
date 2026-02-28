"""CRUD helpers for **CurrentAffairsItem** model.

Includes pgvector similarity search for embedding-based matching.
"""

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select, func, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.current_affair import CurrentAffairsItem
from app.schemas.current_affair import CurrentAffairCreate, CurrentAffairUpdate


class CRUDCurrentAffair(CRUDBase[CurrentAffairsItem, CurrentAffairCreate, CurrentAffairUpdate]):
    """Extended CRUD for current_affairs_items table."""

    async def get_by_category(
        self,
        db: AsyncSession,
        *,
        category: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[CurrentAffairsItem], int]:
        """List items by category with count."""
        base = select(self.model).where(self.model.category == category)
        count_q = select(func.count()).select_from(self.model).where(
            self.model.category == category
        )

        total: int = (await db.execute(count_q)).scalar() or 0
        result = await db.execute(
            base.order_by(self.model.published_date.desc().nullslast())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def get_exam_relevant(
        self,
        db: AsyncSession,
        *,
        min_relevance: float = 0.7,
        limit: int = 50,
    ) -> list[CurrentAffairsItem]:
        """Return items above a relevance threshold."""
        result = await db.execute(
            select(self.model)
            .where(self.model.relevance_score >= min_relevance)
            .order_by(self.model.relevance_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_for_prediction(
        self, db: AsyncSession, *, limit: int = 100
    ) -> list[CurrentAffairsItem]:
        """Return items flagged for inclusion in predictions."""
        result = await db.execute(
            select(self.model)
            .where(self.model.is_included_in_prediction.is_(True))
            .order_by(self.model.published_date.desc().nullslast())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_without_mcq(
        self, db: AsyncSession, *, limit: int = 50
    ) -> list[CurrentAffairsItem]:
        """Return items that haven't had MCQs generated yet."""
        result = await db.execute(
            select(self.model)
            .where(self.model.mcq_generated.is_(False))
            .where(self.model.is_included_in_prediction.is_(True))
            .order_by(self.model.relevance_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_similar(
        self,
        db: AsyncSession,
        *,
        embedding: list[float],
        limit: int = 10,
        threshold: float = 0.80,
    ) -> list[dict[str, Any]]:
        """Cosine similarity search on current affairs embeddings."""
        vec_literal = f"[{','.join(str(v) for v in embedding)}]"

        stmt = (
            select(
                self.model,
                sa_text(f"1 - (embedding <=> '{vec_literal}'::vector) AS similarity"),
            )
            .where(self.model.embedding.isnot(None))
            .order_by(sa_text(f"embedding <=> '{vec_literal}'::vector"))
            .limit(limit)
        )

        result = await db.execute(stmt)
        rows = result.all()

        return [
            {"item": row[0], "similarity_score": float(row[1])}
            for row in rows
            if float(row[1]) >= threshold
        ]

    async def set_embedding(
        self, db: AsyncSession, *, id: UUID, embedding: list[float]
    ) -> CurrentAffairsItem:
        """Store the embedding vector for an item."""
        obj = await self.get_or_404(db, id=id)
        obj.embedding = embedding  # type: ignore[assignment]
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj


crud_current_affair = CRUDCurrentAffair(CurrentAffairsItem)
