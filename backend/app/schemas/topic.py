"""Topic schemas — matches Topic ORM model."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class TopicBase(BaseModel):
    name: str
    display_name: str
    description: str | None = None
    color_hex: str | None = None
    icon: str | None = None
    parent_topic_id: UUID | None = None


class TopicCreate(TopicBase):
    pass


class TopicUpdate(BaseModel):
    name: str | None = None
    display_name: str | None = None
    description: str | None = None
    color_hex: str | None = None
    icon: str | None = None
    parent_topic_id: UUID | None = None


class TopicResponse(TopicBase):
    id: UUID
    total_questions: int
    last_appeared_date: date | None = None
    first_appeared_date: date | None = None
    frequency_score: float
    trend_direction: str | None = None
    story_document: str | None = None
    story_last_updated: datetime | None = None
    story_word_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TopicListResponse(BaseModel):
    topics: list[TopicResponse] = []
    total: int = 0
