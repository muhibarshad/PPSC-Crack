"""
Story Document schemas — request / response models for the story generation API.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# ── Trigger request ──────────────────────────────────────────

class StoryGenerateRequest(BaseModel):
    """Body for POST /stories/generate/{topic_id}."""
    force: bool = False


# ── Task status ──────────────────────────────────────────────

class StoryTaskResponse(BaseModel):
    """Response after enqueuing a story generation task."""
    task_id: str
    topic_id: UUID
    status: str = "queued"
    message: str = "Story generation task enqueued."


class StoryBatchTaskResponse(BaseModel):
    """Response after enqueuing a batch story generation task."""
    task_id: str
    status: str = "queued"
    message: str = "Batch story generation task enqueued."


# ── Story document detail ────────────────────────────────────

class StoryDocumentResponse(BaseModel):
    """Full story document for a topic."""
    topic_id: UUID
    topic_name: str
    display_name: str
    story_document: str | None = None
    story_word_count: int = 0
    story_last_updated: datetime | None = None
    total_questions: int = 0

    model_config = {"from_attributes": True}


# ── Eligible topics list ─────────────────────────────────────

class EligibleTopicItem(BaseModel):
    """A topic eligible for story generation."""
    topic_id: UUID
    display_name: str
    question_count: int
    has_story: bool


class EligibleTopicsResponse(BaseModel):
    """List of topics eligible for story generation."""
    topics: list[EligibleTopicItem] = []
    total: int = 0


# ── Incremental update ───────────────────────────────────────

class IncrementalUpdateRequest(BaseModel):
    """Body for POST /stories/update/{topic_id}/paper/{paper_id}."""
    pass  # No extra fields needed; topic_id + paper_id come from path


class IncrementalFactsUpdateRequest(BaseModel):
    """Body for POST /stories/update/{topic_id}/facts — manual fact injection."""
    facts: list[str]


class FactRouting(BaseModel):
    """How a single fact was routed to a section."""
    fact: str
    similarity: float


class IncrementalUpdateResponse(BaseModel):
    """Response after an incremental story update completes or is enqueued."""
    task_id: str
    topic_id: UUID
    paper_id: UUID | None = None
    status: str = "queued"
    message: str = "Incremental story update task enqueued."
