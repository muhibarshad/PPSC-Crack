"""
Admin Papers Library — Response/Request schemas.
=================================================
Supports the /admin/papers endpoints for paper management.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Topic pill (for paper card) ──────────────────────────────
class TopicPill(BaseModel):
    id: UUID
    name: str
    display_name: str
    color_hex: str | None = None


# ── Paper card response ──────────────────────────────────────
class AdminPaperCard(BaseModel):
    id: UUID
    title: str
    paper_year: int
    paper_month: int | None = None
    paper_date: datetime | None = None
    total_questions: int = 0
    ingestion_status: str  # pending | processing | completed | failed
    repeat_questions_count: int = 0

    # Job type info
    job_type_id: UUID
    job_type_name: str
    job_type_slug: str

    # Topics covered (max 5 shown, + rest count)
    topics: list[TopicPill] = []
    topics_total: int = 0

    source: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class AdminPapersListResponse(BaseModel):
    papers: list[AdminPaperCard] = []
    total: int = 0
    page: int = 1
    per_page: int = 20


# ── Paper detail (single paper) ─────────────────────────────
class QuestionInPaper(BaseModel):
    id: UUID
    question_number: int
    question_text: str
    option_a: str | None = None
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None
    correct_answer: str | None = None
    topic_id: UUID | None = None
    topic_name: str | None = None
    subtopic: str | None = None
    difficulty_score: float = 0.5
    fact_extracted: str | None = None
    is_repeated: bool = False
    repeat_count: int = 0
    needs_review: bool = True
    admin_notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminPaperDetail(BaseModel):
    id: UUID
    title: str
    paper_year: int
    paper_month: int | None = None
    paper_date: datetime | None = None
    total_questions: int = 0
    ingestion_status: str
    source: str | None = None
    raw_scan_data: dict | None = None

    # Job type
    job_type_id: UUID
    job_type_name: str
    job_type_slug: str

    # All topics
    topics: list[TopicPill] = []

    # Questions (paginated)
    questions: list[QuestionInPaper] = []
    questions_total: int = 0
    questions_page: int = 1
    questions_per_page: int = 20

    repeat_questions_count: int = 0
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Update paper ─────────────────────────────────────────────
class AdminPaperUpdate(BaseModel):
    title: str | None = None
    paper_year: int | None = None
    paper_month: int | None = None
    source: str | None = None
    ingestion_status: str | None = None


# ── Update question inline ───────────────────────────────────
class AdminQuestionUpdate(BaseModel):
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
    needs_review: bool | None = None
    admin_notes: str | None = None


class ReprocessResponse(BaseModel):
    paper_id: UUID
    status: str
    message: str
    task_id: str | None = None
