"""Paper schemas — matches Paper ORM model."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PaperBase(BaseModel):
    job_type_id: UUID
    title: str
    paper_year: int
    paper_month: int | None = None
    source: str | None = None


class PaperCreate(PaperBase):
    paper_date: datetime | None = None
    raw_scan_data: dict | None = None


class PaperUpdate(BaseModel):
    title: str | None = None
    paper_year: int | None = None
    paper_month: int | None = None
    source: str | None = None
    ingestion_status: str | None = None
    raw_scan_data: dict | None = None


class PaperResponse(PaperBase):
    id: UUID
    paper_date: datetime | None = None
    total_questions: int
    ingestion_status: str
    raw_scan_data: dict | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class PaperListResponse(BaseModel):
    papers: list[PaperResponse] = []
    total: int = 0
    page: int = 1
    per_page: int = 20
