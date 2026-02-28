"""Admin-note schemas — matches AdminNote ORM model."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AdminNoteBase(BaseModel):
    raw_content: str = Field(..., min_length=10, description="Raw note content to process")
    source_description: str | None = Field(None, max_length=500, description="Where this note came from")


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
    # Topic info (populated via relationship)
    topic_name: str | None = None
    topic_display_name: str | None = None

    model_config = {"from_attributes": True}


class AdminNoteListResponse(BaseModel):
    notes: list[AdminNoteResponse] = []
    total: int = 0
    page: int = 1
    per_page: int = 20


class AdminNoteUploadResponse(BaseModel):
    """Response for POST /admin/notes — upload + trigger processing."""
    id: UUID
    status: str = "queued"
    task_id: str | None = None
    message: str = "Note uploaded and queued for AI processing"


class AdminNoteProcessingResult(BaseModel):
    """Result summary from the AI processing pipeline."""
    status: str
    note_id: str
    topic_name: str | None = None
    topic_id: str | None = None
    facts_count: int = 0
    facts: list[str] = []
    story_section: str | None = None
    position_in_story: int | None = None
    story_task_id: str | None = None
