"""Dashboard schemas — response models for GET /dashboard/home."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# Progress Ring
# ═══════════════════════════════════════════════════════════

class ProgressRingData(BaseModel):
    """Overall exam readiness based on topics completed vs total."""
    topics_completed: int = 0
    topics_total: int = 0
    readiness_percent: float = 0.0


# ═══════════════════════════════════════════════════════════
# Streak
# ═══════════════════════════════════════════════════════════

class StreakData(BaseModel):
    """Consecutive days studied."""
    current_streak: int = 0
    longest_streak: int = 0
    studied_today: bool = False


# ═══════════════════════════════════════════════════════════
# Action cards
# ═══════════════════════════════════════════════════════════

class TodaysFocusTopic(BaseModel):
    """Highest-predicted-weight topic for the student's primary job."""
    topic_id: UUID
    topic_name: str
    display_name: str
    percentage: float = 0.0
    trend_direction: str | None = None
    icon: str | None = None


class LatestPredictedPaper(BaseModel):
    """Most recently published predicted paper (premium only)."""
    prediction_id: UUID
    title: str
    prediction_date: date
    confidence_score: float = 0.0
    total_questions: int = 0
    job_type_name: str = ""


class NextStoryToRead(BaseModel):
    """The next unread story document the student should tackle."""
    topic_id: UUID
    topic_name: str
    display_name: str
    story_word_count: int = 0
    estimated_read_minutes: int = 0
    frequency_score: float = 0.0


# ═══════════════════════════════════════════════════════════
# Quick stats
# ═══════════════════════════════════════════════════════════

class QuickStats(BaseModel):
    topics_completed: int = 0
    questions_practiced: int = 0
    days_active: int = 0


# ═══════════════════════════════════════════════════════════
# Full dashboard response
# ═══════════════════════════════════════════════════════════

class DashboardHomeResponse(BaseModel):
    """Complete payload for the student dashboard home page."""
    greeting_name: str = ""
    subscription_tier: str = "free"
    is_premium: bool = False

    progress: ProgressRingData = Field(default_factory=ProgressRingData)
    streak: StreakData = Field(default_factory=StreakData)
    quick_stats: QuickStats = Field(default_factory=QuickStats)

    todays_focus: TodaysFocusTopic | None = None
    latest_prediction: LatestPredictedPaper | None = None
    next_story: NextStoryToRead | None = None

    selected_job_names: list[str] = Field(default_factory=list)
