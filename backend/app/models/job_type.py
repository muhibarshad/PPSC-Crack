"""
JobType model — PPSC job categories (Clerk, ASI, Tehsildar, etc.).
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Float, Boolean, DateTime, JSON, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobType(Base):
    __tablename__ = "job_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    department: Mapped[str | None] = mapped_column(String(200), nullable=True)
    total_papers: Mapped[int] = mapped_column(Integer, default=0)
    avg_questions_per_paper: Mapped[float] = mapped_column(Float, default=0.0)
    topic_ratios: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_updated_ratios: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────
    papers = relationship("Paper", back_populates="job_type_rel", lazy="selectin")
    pattern_snapshots = relationship("PatternSnapshot", back_populates="job_type_rel", lazy="selectin")
    topic_frequencies = relationship("TopicFrequencyByJob", back_populates="job_type_rel", lazy="selectin")

    def __repr__(self) -> str:
        return f"<JobType id={self.id} slug={self.slug!r}>"
