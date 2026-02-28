"""
Review Queue schemas — enriched question data for admin review UI.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewQueueItem(BaseModel):
    """A single question that needs admin review, enriched with paper context."""

    # ── Question fields ──────────────────────────
    id: UUID
    paper_id: UUID
    question_number: int
    question_text: str
    option_a: str | None = None
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None
    correct_answer: str | None = None
    topic_id: UUID | None = None
    subtopic: str | None = None
    difficulty_score: float = 0.5
    fact_extracted: str | None = None
    year_appeared: int | None = None
    is_repeated: bool = False
    repeat_count: int = 0
    similarity_group_id: UUID | None = None
    needs_review: bool = True
    admin_notes: str | None = None
    created_at: datetime

    # ── Paper context ────────────────────────────
    paper_title: str
    paper_year: int
    paper_month: int | None = None
    job_type_name: str | None = None
    raw_scan_data: dict | None = None

    # ── Topic context (if already classified) ────
    topic_name: str | None = None
    topic_display_name: str | None = None

    model_config = {"from_attributes": True}


class ReviewQueueResponse(BaseModel):
    """Paginated review queue response."""

    items: list[ReviewQueueItem] = []
    total: int = 0
    page: int = 1
    per_page: int = 50


class QuestionCorrection(BaseModel):
    """Payload an admin sends to correct a question."""

    question_text: str | None = None
    option_a: str | None = None
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None
    correct_answer: str | None = Field(None, pattern=r"^[abcd]$")
    topic_id: UUID | None = None
    subtopic: str | None = None
    difficulty_score: float | None = None
    fact_extracted: str | None = None
    admin_notes: str | None = None


class QuestionCorrectionResponse(BaseModel):
    """Response after correcting a question."""

    id: UUID
    needs_review: bool
    admin_notes: str | None = None
    embedding_updated: bool = False
    message: str = "Question updated successfully"
