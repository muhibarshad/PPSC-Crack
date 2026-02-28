"""
PatternSnapshot — periodic AI-generated analysis snapshots per job type.
"""

import uuid
from datetime import datetime, date

from sqlalchemy import Integer, Float, DateTime, Date, JSON, ForeignKey, Index, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PatternSnapshot(Base):
    __tablename__ = "pattern_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    job_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_types.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    paper_count_at_snapshot: Mapped[int] = mapped_column(Integer, default=0)
    predicted_topic_ratios: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    high_probability_facts: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    current_affairs_patterns: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────
    job_type_rel = relationship("JobType", back_populates="pattern_snapshots", lazy="selectin")

    # ── Indexes ──────────────────────────────────────────────
    __table_args__ = (
        Index("ix_ps_job_type_id", "job_type_id"),
        Index("ix_ps_snapshot_date", "snapshot_date"),
        Index("ix_ps_job_date", "job_type_id", "snapshot_date"),
    )

    def __repr__(self) -> str:
        return f"<PatternSnapshot id={self.id} job={self.job_type_id} date={self.snapshot_date}>"
