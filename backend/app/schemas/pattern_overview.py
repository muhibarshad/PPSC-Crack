"""Pattern overview schemas — response models for GET /patterns/overview."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TopicTrend(BaseModel):
    """Single topic trend entry."""
    topic_id: UUID
    topic_name: str
    display_name: str
    percentage: float = 0.0
    question_count: int = 0
    trend_direction: str | None = None  # rising | falling | stable


class DueTopic(BaseModel):
    """Topic flagged as 'due' — absent from recent papers."""
    topic_id: UUID
    topic_name: str
    display_name: str
    absent_papers: int = 0


class HighFrequencyFact(BaseModel):
    """Fact appearing in 3+ papers."""
    fact: str
    paper_count: int
    total_appearances: int


class RepeatQuestionSummary(BaseModel):
    """Summary of repeat-question groups."""
    total_groups: int = 0
    total_repeated_questions: int = 0


class PatternOverviewResponse(BaseModel):
    """Full pattern-intelligence overview for a job type."""
    job_type_id: UUID
    job_type_name: str
    snapshot_date: date | None = None
    paper_count: int = 0
    confidence_score: float = 0.0

    # Topic frequency & trends
    topic_trends: list[TopicTrend] = Field(default_factory=list)

    # Due topics
    due_topics: list[DueTopic] = Field(default_factory=list)

    # High-frequency facts
    high_frequency_facts: list[HighFrequencyFact] = Field(default_factory=list)

    # Repeat questions
    repeat_summary: RepeatQuestionSummary = Field(
        default_factory=RepeatQuestionSummary
    )

    # Raw predicted ratios from latest snapshot
    predicted_topic_ratios: dict[str, Any] | None = None

    # Snapshot metadata
    snapshot_id: UUID | None = None
    snapshot_created_at: datetime | None = None

    model_config = {"from_attributes": True}
