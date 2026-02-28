"""CRUD helpers for **AdminNote** model.

Includes pgvector similarity search for content matching.
"""

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select, func, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.admin_note import AdminNote
from app.schemas.admin_note import AdminNoteCreate, AdminNoteUpdate


class CRUDAdminNote(CRUDBase[AdminNote, AdminNoteCreate, AdminNoteUpdate]):
    """Extended CRUD for admin_notes table."""

    async def get_unprocessed(
        self, db: AsyncSession, *, limit: int = 50
    ) -> list[AdminNote]:
        """Return notes that haven't been processed yet."""
        result = await db.execute(
            select(self.model)
            .where(self.model.processed.is_(False))
            .order_by(self.model.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_topic(
        self,
        db: AsyncSession,
        *,
        topic_id: UUID,
        processed_only: bool = False,
    ) -> Sequence[AdminNote]:
        """Return notes assigned to a specific topic."""
        query = select(self.model).where(self.model.assigned_topic_id == topic_id)
        if processed_only:
            query = query.where(self.model.processed.is_(True))
        query = query.order_by(self.model.position_in_story.asc().nullslast())
        result = await db.execute(query)
        return result.scalars().all()

    async def get_story_pieces(
        self, db: AsyncSession, *, topic_id: UUID
    ) -> Sequence[AdminNote]:
        """Return processed notes for a topic, ordered for story assembly."""
        result = await db.execute(
            select(self.model)
            .where(self.model.assigned_topic_id == topic_id)
            .where(self.model.processed.is_(True))
            .order_by(self.model.position_in_story.asc().nullslast())
        )
        return result.scalars().all()

    async def mark_processed(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        processed_content: str,
        topic_id: UUID | None = None,
        position: int | None = None,
    ) -> AdminNote:
        """Mark a note as processed with its derived content."""
        update_data: dict[str, Any] = {
            "processed": True,
            "processed_content": processed_content,
        }
        if topic_id is not None:
            update_data["assigned_topic_id"] = topic_id
        if position is not None:
            update_data["position_in_story"] = position
        return await self.update(db, id=id, obj_in=update_data)

    async def find_similar(
        self,
        db: AsyncSession,
        *,
        embedding: list[float],
        limit: int = 10,
        threshold: float = 0.80,
    ) -> list[dict[str, Any]]:
        """Cosine similarity search on admin note embeddings."""
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
            {"note": row[0], "similarity_score": float(row[1])}
            for row in rows
            if float(row[1]) >= threshold
        ]

    async def set_embedding(
        self, db: AsyncSession, *, id: UUID, embedding: list[float]
    ) -> AdminNote:
        """Store the embedding vector for a note."""
        obj = await self.get_or_404(db, id=id)
        obj.embedding = embedding  # type: ignore[assignment]
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj


crud_admin_note = CRUDAdminNote(AdminNote)
