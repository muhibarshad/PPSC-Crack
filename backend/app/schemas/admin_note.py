"""Admin-note schemas — matches AdminNote ORM model."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AdminNoteBase(BaseModel):
    raw_content: str
    source_description: str | None = None


class AdminNoteCreate(AdminNoteBase):
    assigned_topic_id: UUID | None = None


class AdminNoteUpdate(BaseModel):
    raw_content: str | None = None
    processed: bool | None = None
    assigned_topic_id: UUID | None = None
    processed_content: str | None = None
    position_in_story: int | None = None
    source_description: str | None = None


class AdminNoteResponse(AdminNoteBase):
    id: UUID
    processed: bool
    assigned_topic_id: UUID | None = None
    processed_content: str | None = None
    position_in_story: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminNoteListResponse(BaseModel):
    notes: list[AdminNoteResponse] = []
    total: int = 0
    page: int = 1
    per_page: int = 20
