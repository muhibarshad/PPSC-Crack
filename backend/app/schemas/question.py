"""Question schemas — matches Question ORM model."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class QuestionBase(BaseModel):
    question_number: int
    question_text: str
    option_a: str | None = None
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None
    correct_answer: str | None = Field(None, pattern=r"^[abcd]$")


class QuestionCreate(QuestionBase):
    paper_id: UUID
    topic_id: UUID | None = None
    subtopic: str | None = None
    difficulty_score: float = 0.5
    fact_extracted: str | None = None
    year_appeared: int | None = None


class QuestionUpdate(BaseModel):
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
    is_repeated: bool | None = None
    repeat_count: int | None = None
    similarity_group_id: UUID | None = None
    needs_review: bool | None = None
    admin_notes: str | None = None


class QuestionResponse(QuestionBase):
    id: UUID
    paper_id: UUID
    topic_id: UUID | None = None
    subtopic: str | None = None
    difficulty_score: float
    fact_extracted: str | None = None
    year_appeared: int | None = None
    is_repeated: bool
    repeat_count: int
    similarity_group_id: UUID | None = None
    needs_review: bool
    admin_notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionListResponse(BaseModel):
    questions: list[QuestionResponse] = []
    total: int = 0
    page: int = 1
    per_page: int = 20


class SimilarQuestionResult(BaseModel):
    """Returned by vector-similarity search."""
    question: QuestionResponse
    similarity_score: float
