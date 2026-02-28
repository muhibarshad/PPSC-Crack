"""
Scan Upload Schemas
====================
Request/response models for ``POST /api/v1/admin/papers/upload-scan``.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


# ── Response ─────────────────────────────────────────────────

class ScanImageInfo(BaseModel):
    """Info about a single uploaded scan image."""
    label: str
    url: str
    size_bytes: int


class OCRStats(BaseModel):
    """OCR extraction statistics."""
    questions_extracted: int = 0
    answers_extracted: int = 0
    answers_mapped: int = 0
    unmapped_questions: list[int] = []


class ReviewStats(BaseModel):
    """Review queue statistics for this paper."""
    total_questions: int = 0
    needs_review: int = 0
    auto_approved: int = 0
    confidence_threshold: float = 0.85


class ScanUploadResponse(BaseModel):
    """Response after scan upload + OCR processing."""

    paper_id: UUID
    ingestion_status: str = "processing"
    task_id: str | None = Field(None, description="Celery task ID for AI pipeline progress")
    images: list[ScanImageInfo] = []
    ocr_stats: OCRStats = OCRStats()
    review_stats: ReviewStats = ReviewStats()
    warnings: list[str] = []
    sync_processing_time_ms: float = 0.0
    message: str = "Scan processed. AI pipeline started in background."
