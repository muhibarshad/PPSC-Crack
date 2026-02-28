"""
Story Reader schemas — request / response models for the immersive story reader.
==================================================================================
GET  /api/v1/student/topics/{id}/story     → full story + high-freq facts + quiz
POST /api/v1/student/topics/{id}/progress  → save reading progress
POST /api/v1/student/topics/{id}/quiz      → generate section quiz via GPT-4o
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# Quiz Models
# ═══════════════════════════════════════════════════════════

class QuizOption(BaseModel):
    """A single MCQ option."""
    label: str          # "A", "B", "C", "D"
    text: str


class QuizQuestion(BaseModel):
    """A single quiz question for a story section."""
    id: str
    question: str
    options: list[QuizOption]
    correct_answer: str  # "A", "B", "C", or "D"
    explanation: str = ""


class SectionQuiz(BaseModel):
    """Quiz for a specific story section."""
    section_index: int
    questions: list[QuizQuestion] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════
# High-frequency Fact
# ═══════════════════════════════════════════════════════════

class HighFreqFact(BaseModel):
    """A fact that appeared in 3+ papers for this topic."""
    fact_text: str
    repeat_count: int
    question_text: str | None = None


# ═══════════════════════════════════════════════════════════
# Bookmark & Note
# ═══════════════════════════════════════════════════════════

class BookmarkData(BaseModel):
    """A bookmarked paragraph."""
    paragraph_index: int
    text_preview: str = ""
    created_at: str = ""


class InlineNote(BaseModel):
    """A personal note attached to a section."""
    section_index: int
    note_text: str
    created_at: str = ""


# ═══════════════════════════════════════════════════════════
# Full Story Reader Response
# ═══════════════════════════════════════════════════════════

class StoryReaderResponse(BaseModel):
    """Complete payload for the immersive story reader."""
    topic_id: UUID
    topic_name: str
    display_name: str
    story_document: str | None = None
    story_word_count: int = 0
    story_last_updated: datetime | None = None
    total_questions: int = 0
    frequency_score: float = 0.0
    color_hex: str | None = None
    icon: str | None = None

    # High-frequency facts (repeat_count >= 3)
    high_freq_facts: list[HighFreqFact] = Field(default_factory=list)

    # Saved reading progress
    reading_progress: float = 0.0       # 0.0 — 1.0
    sections_unlocked: int = 1          # first section always unlocked
    bookmarks: list[BookmarkData] = Field(default_factory=list)
    notes: list[InlineNote] = Field(default_factory=list)

    # Pre-generated quizzes (if any exist)
    quizzes: list[SectionQuiz] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# Save Progress Request
# ═══════════════════════════════════════════════════════════

class SaveProgressRequest(BaseModel):
    """POST body for saving reading progress."""
    reading_progress: float = 0.0           # 0.0 — 1.0
    sections_unlocked: int = 1
    bookmarks: list[BookmarkData] = Field(default_factory=list)
    notes: list[InlineNote] = Field(default_factory=list)
    completed: bool = False


class SaveProgressResponse(BaseModel):
    """Confirmation after saving progress."""
    topic_id: UUID
    saved: bool = True
    message: str = "Progress saved successfully."


# ═══════════════════════════════════════════════════════════
# Generate Quiz Request / Response
# ═══════════════════════════════════════════════════════════

class GenerateQuizRequest(BaseModel):
    """Request body for generating a section quiz."""
    section_index: int
    section_text: str


class GenerateQuizResponse(BaseModel):
    """Response with generated quiz questions."""
    topic_id: UUID
    section_index: int
    quiz: SectionQuiz
