"""
Paper Ingestion Schemas
========================
Request/response models for the ``POST /api/v1/admin/papers`` endpoint.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request ──────────────────────────────────────────────────

class PaperIngestRequest(BaseModel):
    """Admin pastes the full paper text + answer key for ingestion."""

    job_type_id: UUID = Field(..., description="UUID of the target job type")
    paper_year: int = Field(..., ge=1990, le=2100, description="Year the paper was conducted")
    paper_month: int | None = Field(None, ge=1, le=12, description="Month (optional)")
    title: str = Field(
        ..., min_length=3, max_length=500,
        description="Paper title, e.g. 'PPSC Clerk 2024 Batch 1'",
    )
    questions_text: str = Field(
        ..., min_length=50,
        description="Raw text of all 100 MCQs (pasted)",
    )
    answer_key_text: str = Field(
        ..., min_length=10,
        description="Raw text of the answer key (pasted)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "job_type_id": "550e8400-e29b-41d4-a716-446655440000",
                    "paper_year": 2024,
                    "paper_month": 6,
                    "title": "PPSC Clerk 2024 Batch 1",
                    "questions_text": "1. What is the capital of Pakistan?\nA) Lahore\nB) Karachi\nC) Islamabad\nD) Peshawar\n\n2. ...",
                    "answer_key_text": "1-C 2-A 3-B 4-D ...",
                }
            ]
        }
    }


# ── Response ─────────────────────────────────────────────────

class ParseSummary(BaseModel):
    total_parsed: int
    total_mapped: int
    unmapped_questions: list[int] = []
    unmapped_answers: list[int] = []
    warnings: list[str] = []


class PaperIngestResponse(BaseModel):
    """Immediate response after sync parsing; AI pipeline runs in background."""

    paper_id: UUID
    ingestion_status: str = "processing"
    task_id: str | None = Field(None, description="Celery task ID for polling progress")
    parse_summary: ParseSummary
    sync_processing_time_ms: float
    message: str = "Paper parsed successfully. AI processing started in background."


# ── Polling / Status ─────────────────────────────────────────

class IngestionStatusResponse(BaseModel):
    paper_id: UUID
    ingestion_status: str
    task_id: str | None = None
    task_state: str | None = None
    ai_summary: dict | None = None


# ── AI step details (returned when task is complete) ─────────

class ClassificationSummary(BaseModel):
    classified: int = 0
    total: int = 0
    new_topics: int = 0
    time_ms: float = 0.0


class FactExtractionSummary(BaseModel):
    extracted: int = 0
    total: int = 0
    time_ms: float = 0.0


class EmbeddingSummary(BaseModel):
    generated: int = 0
    time_ms: float = 0.0


class SimilarityMatch(BaseModel):
    new_question_number: int
    new_question_id: str
    matched_question_id: str
    similarity: float
    group_id: str


class SimilaritySummary(BaseModel):
    duplicates_found: int = 0
    details: list[SimilarityMatch] = []
    time_ms: float = 0.0


class PatternUpdateSummary(BaseModel):
    topics_updated: int = 0
    time_ms: float = 0.0


class AIProcessingSummary(BaseModel):
    paper_id: str
    status: str
    total_ai_processing_time_ms: float = 0.0
    steps: dict = {}
