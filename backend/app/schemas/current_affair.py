"""Current affairs schemas."""

from datetime import datetime

from pydantic import BaseModel


class CurrentAffairBase(BaseModel):
    title: str
    category: str
    content: str
    is_exam_relevant: bool = True


class CurrentAffairCreate(CurrentAffairBase):
    summary: str | None = None
    source_url: str | None = None


class CurrentAffairResponse(CurrentAffairBase):
    id: int
    summary: str | None = None
    source_url: str | None = None
    published_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
