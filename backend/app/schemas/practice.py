"""
Practice Test schemas — request / response models for the practice test system.
==================================================================================
GET  /api/v1/student/practice/generate  → generate a practice set
POST /api/v1/student/practice/submit    → submit answers & get scored results
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# Generate Practice Test
# ═══════════════════════════════════════════════════════════

class PracticeGenerateParams(BaseModel):
    """Query params for generating a practice test."""
    topic_id: UUID | None = None              # None = Full Paper Mode (random across all topics)
    num_questions: int = Field(25, ge=5, le=100)
    timed: bool = False


class PracticeQuestionOut(BaseModel):
    """A single question sent to the frontend (correct answer NOT included)."""
    id: UUID
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    topic_id: UUID | None = None
    topic_name: str | None = None
    difficulty_score: float = 0.5

    model_config = {"from_attributes": True}


class PracticeGenerateResponse(BaseModel):
    """Payload returned when a practice set is generated."""
    test_id: str                              # UUID string to track this attempt
    questions: list[PracticeQuestionOut]
    total_questions: int
    time_limit_seconds: int | None = None     # None if untimed


# ═══════════════════════════════════════════════════════════
# Submit Practice Test
# ═══════════════════════════════════════════════════════════

class PracticeAnswer(BaseModel):
    """A single answer from the student."""
    question_id: UUID
    selected_answer: str = Field(..., pattern=r"^[abcd]$")  # a | b | c | d


class PracticeSubmitRequest(BaseModel):
    """POST body for submitting a completed practice test."""
    test_id: str
    answers: list[PracticeAnswer]
    time_taken_seconds: int = 0


# ═══════════════════════════════════════════════════════════
# Results Breakdown
# ═══════════════════════════════════════════════════════════

class TopicPerformance(BaseModel):
    """Score breakdown per topic."""
    topic_id: UUID | None = None
    topic_name: str
    correct: int
    total: int
    percentage: float


class WrongAnswerDetail(BaseModel):
    """Details of a wrong answer for review."""
    question_id: UUID
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    selected_answer: str
    correct_answer: str
    topic_name: str | None = None
    explanation: str | None = None            # fact_extracted or a hint


class PracticeSubmitResponse(BaseModel):
    """Full results payload returned after scoring."""
    test_id: str
    score: int
    total: int
    percentage: float
    time_taken_seconds: int
    topic_breakdown: list[TopicPerformance]
    wrong_answers: list[WrongAnswerDetail]
