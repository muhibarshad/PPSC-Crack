"""Learning-path schemas — response models for GET /dashboard/learning-path/{job_type_id}."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class LearningPathTopic(BaseModel):
    """Single topic node in the learning-path roadmap."""

    topic_id: UUID
    topic_name: str
    display_name: str
    icon: str | None = None
    color_hex: str | None = None

    # Exam analytics
    frequency_percentage: float = 0.0
    trend_direction: str | None = None
    is_hot: bool = False

    # Story reading
    story_word_count: int = 0
    estimated_read_minutes: int = 0
    has_story: bool = False

    # Student progress: "completed" | "in-progress" | "not-started"
    status: str = "not-started"
    progress_percent: float = 0.0

    # Position in roadmap (1-based)
    rank: int = 0


class LearningPathResponse(BaseModel):
    """Full payload for the learning-path screen."""

    job_type_id: UUID
    job_type_name: str
    total_topics: int = 0
    completed_count: int = 0
    in_progress_count: int = 0
    overall_percent: float = 0.0
    topics: list[LearningPathTopic] = Field(default_factory=list)
