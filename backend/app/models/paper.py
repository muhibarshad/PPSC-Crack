"""
Paper model — past PPSC exam papers.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Index, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    job_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_types.id", ondelete="CASCADE"), nullable=False
    )
    paper_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paper_year: Mapped[int] = mapped_column(Integer, nullable=False)
    paper_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    ingestion_status: Mapped[str] = mapped_column(
        String(50), default="pending",
        comment="pending | processing | completed | failed"
    )
    raw_scan_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ──────────────────────────────────────
    job_type_rel = relationship("JobType", back_populates="papers", lazy="selectin")
    questions = relationship("Question", back_populates="paper_rel", lazy="selectin", cascade="all, delete-orphan")

    # ── Indexes ──────────────────────────────────────────────
    __table_args__ = (
        Index("ix_papers_job_type_year", "job_type_id", "paper_year"),
        Index("ix_papers_ingestion_status", "ingestion_status"),
    )

    def __repr__(self) -> str:
        return f"<Paper id={self.id} title={self.title!r} year={self.paper_year}>"
