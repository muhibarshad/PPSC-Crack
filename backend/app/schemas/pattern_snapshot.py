"""Pattern-snapshot schemas — matches PatternSnapshot ORM model."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class PatternSnapshotBase(BaseModel):
    job_type_id: UUID
    snapshot_date: date


class PatternSnapshotCreate(PatternSnapshotBase):
    paper_count_at_snapshot: int = 0
    predicted_topic_ratios: dict | None = None
    confidence_score: float = 0.0
    high_probability_facts: dict | None = None
    current_affairs_patterns: dict | None = None


class PatternSnapshotResponse(PatternSnapshotBase):
    id: UUID
    paper_count_at_snapshot: int
    predicted_topic_ratios: dict | None = None
    confidence_score: float
    high_probability_facts: dict | None = None
    current_affairs_patterns: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PatternSnapshotListResponse(BaseModel):
    snapshots: list[PatternSnapshotResponse] = []
    total: int = 0
