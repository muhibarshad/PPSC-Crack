"""Paper schemas."""

from datetime import datetime

from pydantic import BaseModel


class PaperBase(BaseModel):
    title: str
    job_type: str
    year: int
    total_questions: int = 0


class PaperCreate(PaperBase):
    content: str | None = None
    source: str | None = None


class PaperResponse(PaperBase):
    id: int
    content: str | None = None
    source: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaperListResponse(BaseModel):
    papers: list[PaperResponse] = []
    total: int = 0
    page: int = 1
    per_page: int = 20
