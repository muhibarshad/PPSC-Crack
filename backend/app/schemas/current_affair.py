"""Current-affairs schemas — matches CurrentAffairsItem ORM model."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class CurrentAffairBase(BaseModel):
    headline: str
    content: str
    category: str
    source_url: str | None = None
    published_date: date | None = None


class CurrentAffairCreate(CurrentAffairBase):
    relevance_score: float = 0.0


class CurrentAffairUpdate(BaseModel):
    headline: str | None = None
    content: str | None = None
    category: str | None = None
    source_url: str | None = None
    published_date: date | None = None
    relevance_score: float | None = None
    is_included_in_prediction: bool | None = None
    mcq_generated: bool | None = None


class CurrentAffairResponse(CurrentAffairBase):
    id: UUID
    relevance_score: float
    is_included_in_prediction: bool
    mcq_generated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CurrentAffairListResponse(BaseModel):
    items: list[CurrentAffairResponse] = []
    total: int = 0
    page: int = 1
    per_page: int = 20
