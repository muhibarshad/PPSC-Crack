"""Current-affairs schemas — matches CurrentAffairsItem ORM model."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Base ─────────────────────────────────────────────────────
class CurrentAffairBase(BaseModel):
    headline: str
    content: str
    category: str
    source_url: str | None = None
    published_date: date | None = None


class CurrentAffairCreate(CurrentAffairBase):
    summary: str | None = None
    source_name: str | None = None
    relevance_score: float = 0.0
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    recency_score: float = 0.0
    category_score: float = 0.0


class CurrentAffairUpdate(BaseModel):
    headline: str | None = None
    content: str | None = None
    summary: str | None = None
    category: str | None = None
    source_url: str | None = None
    published_date: date | None = None
    relevance_score: float | None = None
    is_included_in_prediction: bool | None = None
    is_approved: bool | None = None
    mcq_generated: bool | None = None
    mcq_text: str | None = None
    mcq_options: dict | None = None
    mcq_correct_answer: str | None = None
    mcq_explanation: str | None = None


# ── Student-facing response (no internal scores) ────────────
class CurrentAffairResponse(CurrentAffairBase):
    id: UUID
    summary: str | None = None
    source_name: str | None = None
    relevance_score: float
    is_approved: bool
    mcq_generated: bool
    mcq_text: str | None = None
    mcq_options: dict | None = None
    mcq_correct_answer: str | None = None
    mcq_explanation: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Admin-facing response (includes all scoring details) ────
class CurrentAffairAdminResponse(CurrentAffairResponse):
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    recency_score: float = 0.0
    category_score: float = 0.0
    is_included_in_prediction: bool = False
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CurrentAffairListResponse(BaseModel):
    items: list[CurrentAffairResponse] = []
    total: int = 0
    page: int = 1
    per_page: int = 20


class CurrentAffairAdminListResponse(BaseModel):
    items: list[CurrentAffairAdminResponse] = []
    total: int = 0
    page: int = 1
    per_page: int = 20


# ── Manual add (admin) ──────────────────────────────────────
class CurrentAffairManualAdd(BaseModel):
    headline: str = Field(..., max_length=500)
    content: str
    summary: str | None = None
    category: str = Field(
        ...,
        description="One of: govt_appointment, sports, science, economy, international, records",
    )
    source_url: str | None = None
    published_date: date | None = None
    generate_mcq: bool = Field(
        False, description="Auto-generate MCQ for this item"
    )


# ── Approve action ──────────────────────────────────────────
class CurrentAffairApprove(BaseModel):
    is_approved: bool = True
    is_included_in_prediction: bool = False
