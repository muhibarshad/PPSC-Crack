"""
Admin Dashboard — Response schemas.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# ── Stat Cards ──────────────────────────────────────────────
class AdminStatsResponse(BaseModel):
    total_papers: int = 0
    total_questions: int = 0
    topics_discovered: int = 0
    avg_confidence_score: float = 0.0


# ── Timeline ────────────────────────────────────────────────
class TimelinePaperPoint(BaseModel):
    id: UUID
    title: str
    paper_year: int
    paper_month: int | None = None
    total_questions: int = 0
    ingestion_status: str
    job_type_name: str
    job_type_slug: str
    created_at: datetime


# ── Prediction Health ────────────────────────────────────────
class PredictionHealthItem(BaseModel):
    job_type_id: UUID
    job_type_name: str
    job_type_slug: str
    paper_count: int = 0
    health: str  # "green" | "orange" | "blue"
    confidence_score: float = 0.0


# ── Recent Activity ──────────────────────────────────────────
class RecentActivityItem(BaseModel):
    paper_id: UUID
    title: str
    status: str  # "completed" | "processing" | "pending" | "failed"
    job_type_name: str
    total_questions: int = 0
    created_at: datetime


# ── Combined Response ────────────────────────────────────────
class AdminDashboardResponse(BaseModel):
    stats: AdminStatsResponse
    timeline: list[TimelinePaperPoint]
    prediction_health: list[PredictionHealthItem]
    recent_activity: list[RecentActivityItem]
