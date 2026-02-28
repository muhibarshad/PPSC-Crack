"""
Student Analytics schemas — response models for GET /api/v1/student/analytics.
================================================================================
Powers the /dashboard/analytics page with study-streak calendar, topic
completion bars, quiz score trend, exam readiness, time-studied-per-day,
and readiness comparison data.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# 1. Study Streak Calendar (GitHub-style heatmap)
# ═══════════════════════════════════════════════════════════

class StudyDay(BaseModel):
    """Single day in the 90-day contribution grid."""
    date: date
    minutes_studied: int = 0


# ═══════════════════════════════════════════════════════════
# 2. Topic Completion Bars
# ═══════════════════════════════════════════════════════════

class TopicCompletion(BaseModel):
    """Horizontal bar — % completion for one topic."""
    topic_id: UUID
    topic_name: str
    display_name: str
    completed: bool = False
    weight: float = 0.0          # frequency score (weight)
    completion_percent: float = 0.0


# ═══════════════════════════════════════════════════════════
# 3. Quiz Score Trend
# ═══════════════════════════════════════════════════════════

class QuizScorePoint(BaseModel):
    """One data point on the quiz-score line chart."""
    date: date
    score_percent: float
    total_questions: int = 0


# ═══════════════════════════════════════════════════════════
# 4. Exam Readiness Score
# ═══════════════════════════════════════════════════════════

class ExamReadiness(BaseModel):
    """
    Predicted readiness %:
        (completed_topic_weight / total_topic_weight) × 100

    Where *weight* = sum of topic frequency_score for the student's
    selected job types.
    """
    readiness_percent: float = 0.0
    completed_weight: float = 0.0
    total_weight: float = 0.0
    topics_completed: int = 0
    topics_total: int = 0


# ═══════════════════════════════════════════════════════════
# 5. Time Studied Per Day (bar chart — last 30 days)
# ═══════════════════════════════════════════════════════════

class DailyStudyMinutes(BaseModel):
    date: date
    minutes: int = 0


# ═══════════════════════════════════════════════════════════
# 6. Comparison — user vs peers
# ═══════════════════════════════════════════════════════════

class ReadinessComparison(BaseModel):
    user_readiness: float = 0.0
    average_readiness: float = 0.0
    total_peers: int = 0


# ═══════════════════════════════════════════════════════════
# Full Analytics Response
# ═══════════════════════════════════════════════════════════

class StudentAnalyticsResponse(BaseModel):
    """Complete payload for the /dashboard/analytics page."""
    study_calendar: list[StudyDay] = Field(default_factory=list)
    topic_completions: list[TopicCompletion] = Field(default_factory=list)
    quiz_scores: list[QuizScorePoint] = Field(default_factory=list)
    readiness: ExamReadiness = Field(default_factory=ExamReadiness)
    daily_study_minutes: list[DailyStudyMinutes] = Field(default_factory=list)
    comparison: ReadinessComparison = Field(default_factory=ReadinessComparison)
