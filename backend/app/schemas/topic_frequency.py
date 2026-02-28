"""Topic-frequency schemas — matches TopicFrequencyByJob ORM model."""

from uuid import UUID

from pydantic import BaseModel


class TopicFrequencyBase(BaseModel):
    topic_id: UUID
    job_type_id: UUID
    year: int
    question_count: int = 0
    percentage_of_paper: float = 0.0


class TopicFrequencyCreate(TopicFrequencyBase):
    pass


class TopicFrequencyResponse(TopicFrequencyBase):
    id: UUID

    model_config = {"from_attributes": True}


class TopicFrequencyListResponse(BaseModel):
    frequencies: list[TopicFrequencyResponse] = []
    total: int = 0
