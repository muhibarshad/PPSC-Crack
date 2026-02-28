"""Onboarding schemas — request / response models for student onboarding flow."""

from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# Request
# ═══════════════════════════════════════════════════════════

class OnboardingCompleteRequest(BaseModel):
    """Save selected job types and complete onboarding."""
    selected_job_type_ids: list[UUID] = Field(
        ..., min_length=1, max_length=10,
        description="List of job_type UUIDs the student wants to prepare for",
    )


# ═══════════════════════════════════════════════════════════
# Analysis sub-models (per job type)
# ═══════════════════════════════════════════════════════════

class TopicRatioEntry(BaseModel):
    """Single slice of the radar chart."""
    topic_name: str
    display_name: str
    percentage: float = 0.0
    question_count: int = 0


class JobAnalysis(BaseModel):
    """AI analysis summary for a single job type."""
    job_type_id: UUID
    job_type_name: str
    topic_ratios: list[TopicRatioEntry] = Field(default_factory=list)
    estimated_prep_hours: float = 0.0
    confidence_score: float = 0.0
    total_papers_analyzed: int = 0
    total_topics: int = 0


class OnboardingAnalysisResponse(BaseModel):
    """Aggregated analysis for all selected job types."""
    analyses: list[JobAnalysis] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════
# Learning path preview
# ═══════════════════════════════════════════════════════════

class LearningPathTopic(BaseModel):
    """Single topic in the priority learning path."""
    rank: int
    topic_id: UUID
    topic_name: str
    display_name: str
    frequency_score: float = 0.0
    trend_direction: str | None = None
    story_available: bool = False
    estimated_read_minutes: int = 0


class LearningPathPreview(BaseModel):
    """First 5 topics the student should study."""
    topics: list[LearningPathTopic] = Field(default_factory=list)
    total_topics_in_path: int = 0


# ═══════════════════════════════════════════════════════════
# Complete onboarding response
# ═══════════════════════════════════════════════════════════

class OnboardingCompleteResponse(BaseModel):
    """Response after saving onboarding selections."""
    message: str = "Onboarding complete"
    selected_job_type_ids: list[UUID] = Field(default_factory=list)
    analyses: list[JobAnalysis] = Field(default_factory=list)
    learning_path: LearningPathPreview = Field(default_factory=LearningPathPreview)
