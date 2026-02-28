"""
Topic model — exam topics with frequency analytics & story documents.
"""

import uuid
from datetime import datetime, date

from sqlalchemy import String, Integer, Float, Text, Date, DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    last_appeared_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    first_appeared_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    frequency_score: Mapped[float] = mapped_column(Float, default=0.0)
    trend_direction: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="up | down | stable | new"
    )

    # ── Story document (AI-generated narrative) ──────────────
    story_document: Mapped[str | None] = mapped_column(Text, nullable=True)
    story_last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    story_word_count: Mapped[int] = mapped_column(Integer, default=0)

    # ── UI metadata ──────────────────────────────────────────
    color_hex: Mapped[str | None] = mapped_column(String(7), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── Self-referential hierarchy ───────────────────────────
    parent_topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────
    parent_topic = relationship("Topic", remote_side="Topic.id", lazy="selectin")
    questions = relationship("Question", back_populates="topic_rel", lazy="selectin")
    topic_frequencies = relationship("TopicFrequencyByJob", back_populates="topic_rel", lazy="selectin")
    admin_notes = relationship("AdminNote", back_populates="topic_rel", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Topic id={self.id} name={self.name!r}>"
