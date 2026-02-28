"""Job-type schemas — matches JobType ORM model."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobTypeBase(BaseModel):
    name: str
    slug: str
    department: str | None = None


class JobTypeCreate(JobTypeBase):
    pass


class JobTypeUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    department: str | None = None
    is_active: bool | None = None
    topic_ratios: dict | None = None


class JobTypeTopicRatiosUpdate(BaseModel):
    """Payload for the PATCH /topic-ratios endpoint."""
    topic_ratios: dict


class JobTypeResponse(JobTypeBase):
    id: UUID
    total_papers: int
    avg_questions_per_paper: float
    topic_ratios: dict | None = None
    last_updated_ratios: datetime | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class JobTypeListResponse(BaseModel):
    job_types: list[JobTypeResponse] = []
    total: int = 0
