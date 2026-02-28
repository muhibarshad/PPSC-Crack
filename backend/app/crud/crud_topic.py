"""CRUD helpers for **Topic** model."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.topic import Topic
from app.schemas.topic import TopicCreate, TopicUpdate


class CRUDTopic(CRUDBase[Topic, TopicCreate, TopicUpdate]):
    """Extended CRUD for topics table."""

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Topic | None:
        """Lookup by canonical name (case-sensitive)."""
        result = await db.execute(select(self.model).where(self.model.name == name))
        return result.scalar_one_or_none()

    async def get_top_by_frequency(
        self, db: AsyncSession, *, limit: int = 20
    ) -> list[Topic]:
        """Return topics ordered by frequency_score descending."""
        result = await db.execute(
            select(self.model)
            .order_by(self.model.frequency_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_trending(
        self, db: AsyncSession, *, direction: str = "up", limit: int = 10
    ) -> list[Topic]:
        """Return topics with a specific trend direction."""
        result = await db.execute(
            select(self.model)
            .where(self.model.trend_direction == direction)
            .order_by(self.model.frequency_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_children(
        self, db: AsyncSession, *, parent_id: UUID
    ) -> list[Topic]:
        """Return child topics of a given parent."""
        result = await db.execute(
            select(self.model)
            .where(self.model.parent_topic_id == parent_id)
            .order_by(self.model.name.asc())
        )
        return list(result.scalars().all())

    async def update_story(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        story_document: str,
        word_count: int,
    ) -> Topic:
        """Replace the AI-generated story document."""
        from datetime import datetime, timezone

        return await self.update(
            db,
            id=id,
            obj_in={
                "story_document": story_document,
                "story_word_count": word_count,
                "story_last_updated": datetime.now(timezone.utc),
            },
        )


crud_topic = CRUDTopic(Topic)
