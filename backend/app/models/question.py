"""
Question model — individual MCQs extracted from past papers.
Includes pgvector embedding for semantic similarity / deduplication.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, Index, func, text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, Vector


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False
    )
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str | None] = mapped_column(Text, nullable=True)
    option_b: Mapped[str | None] = mapped_column(Text, nullable=True)
    option_c: Mapped[str | None] = mapped_column(Text, nullable=True)
    option_d: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(
        String(1), nullable=True, comment="a | b | c | d"
    )

    # ── Topic classification ─────────────────────────────────
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    subtopic: Mapped[str | None] = mapped_column(String(200), nullable=True)
    difficulty_score: Mapped[float] = mapped_column(Float, default=0.5, comment="0.0 = easy, 1.0 = hard")

    # ── Extracted intelligence ───────────────────────────────
    fact_extracted: Mapped[str | None] = mapped_column(Text, nullable=True)
    year_appeared: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_repeated: Mapped[bool] = mapped_column(Boolean, default=False)
    repeat_count: Mapped[int] = mapped_column(Integer, default=0)
    similarity_group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # ── pgvector: 1536-dim for OpenAI text-embedding-3-small ─
    embedding: Mapped[Any | None] = mapped_column(Vector(1536), nullable=True)

    # ── Admin review ─────────────────────────────────────────
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────
    paper_rel = relationship("Paper", back_populates="questions", lazy="selectin")
    topic_rel = relationship("Topic", back_populates="questions", lazy="selectin")

    # ── Indexes ──────────────────────────────────────────────
    __table_args__ = (
        Index("ix_questions_paper_id", "paper_id"),
        Index("ix_questions_topic_id", "topic_id"),
        Index("ix_questions_is_repeated", "is_repeated"),
        Index("ix_questions_needs_review", "needs_review"),
        Index("ix_questions_year_appeared", "year_appeared"),
        Index(
            "ix_questions_embedding_hnsw",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<Question id={self.id} paper_id={self.paper_id} q#={self.question_number}>"
