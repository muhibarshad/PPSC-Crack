"""Prediction schemas."""

from datetime import datetime

from pydantic import BaseModel


class PredictionBase(BaseModel):
    job_type: str
    confidence: float = 0.0


class PredictionCreate(PredictionBase):
    topics: dict = {}
    summary: str | None = None


class PredictionResponse(PredictionBase):
    id: int
    topics: dict
    summary: str | None = None
    model_version: str
    generated_at: datetime

    model_config = {"from_attributes": True}
