"""
Prediction Schemas — Request / Response models for the Prediction Engine.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ═════════════════════════════════════════════════════════════
# Request schemas
# ═════════════════════════════════════════════════════════════

class PredictionGenerateRequest(BaseModel):
    """Input for POST /api/admin/predictions/generate."""

    job_type_id: UUID
    prediction_date: date = Field(
        ..., description="Target exam month (e.g. 2026-04-01)"
    )
    include_current_affairs: bool = True
    total_questions: int = Field(
        default=100, ge=10, le=300,
        description="Total MCQs to generate"
    )


class PredictionUpdate(BaseModel):
    """Partial update for PUT /api/admin/predictions/:id."""

    title: str | None = None
    prediction_date: date | None = None
    total_questions: int | None = Field(None, ge=10, le=300)
    include_current_affairs: bool | None = None
    questions_json: dict | None = None
    current_affairs_json: dict | None = None


# ═════════════════════════════════════════════════════════════
# Predicted question (individual MCQ in the prediction)
# ═════════════════════════════════════════════════════════════

class PredictedQuestion(BaseModel):
    """A single AI-generated MCQ in a predicted paper."""

    question_number: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str = Field(..., pattern=r"^[abcd]$")
    topic_name: str
    topic_id: UUID | None = None
    subtopic: str | None = None
    difficulty_score: float = 0.5
    fact_basis: str | None = Field(
        None, description="The high-frequency fact this question tests"
    )
    source_question_id: UUID | None = Field(
        None, description="If inspired by an existing question"
    )
    is_current_affairs: bool = False
    confidence: float = Field(0.0, ge=0.0, le=1.0)


# ═════════════════════════════════════════════════════════════
# Response schemas
# ═════════════════════════════════════════════════════════════

class PredictionResponse(BaseModel):
    """Full prediction detail response."""

    id: UUID
    job_type_id: UUID
    title: str
    prediction_date: date
    total_questions: int
    include_current_affairs: bool
    questions_json: dict | None = None
    current_affairs_json: dict | None = None
    topic_distribution: dict | None = None
    generation_metadata: dict | None = None
    confidence_score: float
    paper_count_basis: int
    pattern_consistency: float
    status: str
    is_published: bool
    published_at: datetime | None = None
    snapshot_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    # Enriched fields
    job_type_name: str | None = None
    question_count_generated: int = 0

    model_config = {"from_attributes": True}


class PredictionListResponse(BaseModel):
    """Paginated list of predictions."""

    items: list[PredictionResponse] = []
    total: int = 0
    page: int = 1
    per_page: int = 20


class PredictionPublishResponse(BaseModel):
    """Response after publishing a prediction."""

    id: UUID
    is_published: bool
    published_at: datetime | None = None
    message: str = "Prediction published successfully"


# ═════════════════════════════════════════════════════════════
# SSE event schemas
# ═════════════════════════════════════════════════════════════

class PredictionSSEEvent(BaseModel):
    """Shape of each SSE event streamed during generation."""

    event: str = Field(
        ..., description="Event type: status | question | current_affair | confidence | complete | error"
    )
    data: dict[str, Any] = Field(default_factory=dict)


class PredictionGenerateResponse(BaseModel):
    """Final result returned via SSE 'complete' event."""

    prediction_id: UUID
    status: str
    total_questions_generated: int
    current_affairs_count: int
    confidence_score: float
    message: str = "Prediction generation complete"
