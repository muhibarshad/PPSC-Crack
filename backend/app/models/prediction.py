"""
Prediction — AI-generated predicted exam papers for upcoming PPSC exams.
"""

import uuid
from datetime import datetime, date
from typing import Any

from sqlalchemy import (
    String, Integer, Float, Boolean, Text, Date, DateTime,
    ForeignKey, Index, JSON, func, text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    job_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_types.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    prediction_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Target exam month/date"
    )
    total_questions: Mapped[int] = mapped_column(Integer, default=100)
    include_current_affairs: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Generated content ────────────────────────────────────
    questions_json: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
        comment="Full array of predicted MCQs [{question_text, options, answer, topic, ...}]"
    )
    current_affairs_json: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
        comment="Current affairs MCQs section"
    )
    topic_distribution: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
        comment="Topic → question count allocation used for generation"
    )
    generation_metadata: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
        comment="Weights, algorithm params, source snapshot, etc."
    )

    # ── Scoring ──────────────────────────────────────────────
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    paper_count_basis: Mapped[int] = mapped_column(
        Integer, default=0, comment="Number of past papers used"
    )
    pattern_consistency: Mapped[float] = mapped_column(
        Float, default=0.0, comment="0.0–1.0 measure of topic pattern stability"
    )

    # ── Status & publishing ──────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(50), default="generating",
        comment="generating | completed | failed | published"
    )
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Reference to pattern snapshot used ───────────────────
    snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pattern_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ──────────────────────────────────────
    job_type_rel = relationship("JobType", backref="predictions", lazy="selectin")
    snapshot_rel = relationship("PatternSnapshot", lazy="selectin")

    # ── Indexes ──────────────────────────────────────────────
    __table_args__ = (
        Index("ix_pred_job_type_id", "job_type_id"),
        Index("ix_pred_prediction_date", "prediction_date"),
        Index("ix_pred_status", "status"),
        Index("ix_pred_is_published", "is_published"),
        Index("ix_pred_job_date", "job_type_id", "prediction_date"),
    )

    def __repr__(self) -> str:
        return f"<Prediction id={self.id} job={self.job_type_id} date={self.prediction_date} status={self.status}>"
