"""CRUD helpers for **Question** model.

Includes pgvector similarity search for embedding-based dedup.
"""

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select, func, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.question import Question
from app.schemas.question import QuestionCreate, QuestionUpdate


class CRUDQuestion(CRUDBase[Question, QuestionCreate, QuestionUpdate]):
    """Extended CRUD for questions table with vector search."""

    async def get_by_paper(
        self,
        db: AsyncSession,
        *,
        paper_id: UUID,
        skip: int = 0,
        limit: int = 200,
    ) -> tuple[Sequence[Question], int]:
        """List questions for a specific paper with count."""
        base = select(self.model).where(self.model.paper_id == paper_id)
        count_q = select(func.count()).select_from(self.model).where(
            self.model.paper_id == paper_id
        )

        total: int = (await db.execute(count_q)).scalar() or 0
        result = await db.execute(
            base.order_by(self.model.question_number.asc()).offset(skip).limit(limit)
        )
        return result.scalars().all(), total

    async def get_by_topic(
        self,
        db: AsyncSession,
        *,
        topic_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Question], int]:
        """List questions classified under a topic."""
        base = select(self.model).where(self.model.topic_id == topic_id)
        count_q = select(func.count()).select_from(self.model).where(
            self.model.topic_id == topic_id
        )

        total: int = (await db.execute(count_q)).scalar() or 0
        result = await db.execute(
            base.order_by(self.model.year_appeared.desc().nullslast())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def get_needing_review(
        self, db: AsyncSession, *, limit: int = 50
    ) -> list[Question]:
        """Return questions flagged for manual review."""
        result = await db.execute(
            select(self.model)
            .where(self.model.needs_review.is_(True))
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_repeated(
        self, db: AsyncSession, *, min_count: int = 2, limit: int = 50
    ) -> list[Question]:
        """Return questions that have been repeated across papers."""
        result = await db.execute(
            select(self.model)
            .where(self.model.is_repeated.is_(True))
            .where(self.model.repeat_count >= min_count)
            .order_by(self.model.repeat_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_similar(
        self,
        db: AsyncSession,
        *,
        embedding: list[float],
        limit: int = 10,
        threshold: float = 0.85,
    ) -> list[dict[str, Any]]:
        """Find semantically similar questions using pgvector cosine distance.

        Returns list of ``{"question": Question, "similarity_score": float}``.
        Lower cosine distance = higher similarity.
        Score is converted to 0-1 similarity (1 - distance).
        """
        # Cast the input embedding to a vector literal
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
            {"question": row[0], "similarity_score": float(row[1])}
            for row in rows
            if float(row[1]) >= threshold
        ]

    async def set_embedding(
        self, db: AsyncSession, *, id: UUID, embedding: list[float]
    ) -> Question:
        """Store the OpenAI embedding vector for a question."""
        obj = await self.get_or_404(db, id=id)
        obj.embedding = embedding  # type: ignore[assignment]
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def mark_reviewed(
        self, db: AsyncSession, *, id: UUID, notes: str | None = None
    ) -> Question:
        """Mark a question as reviewed by an admin."""
        update_data: dict[str, Any] = {"needs_review": False}
        if notes is not None:
            update_data["admin_notes"] = notes
        return await self.update(db, id=id, obj_in=update_data)

    async def get_by_similarity_group(
        self, db: AsyncSession, *, group_id: UUID
    ) -> list[Question]:
        """Return all questions in the same similarity cluster."""
        result = await db.execute(
            select(self.model)
            .where(self.model.similarity_group_id == group_id)
            .order_by(self.model.year_appeared.desc().nullslast())
        )
        return list(result.scalars().all())


crud_question = CRUDQuestion(Question)
