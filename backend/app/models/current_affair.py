"""
CurrentAffairsItem — daily news items scored for exam relevance.
Includes pgvector embedding for semantic similarity matching.
RSS feeds are fetched daily and scored for PPSC exam relevance.
"""

import uuid
from datetime import datetime, date
from typing import Any

from sqlalchemy import String, Float, Boolean, Text, Date, DateTime, Index, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, Vector


class CurrentAffairsItem(Base):
    __tablename__ = "current_affairs_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True, comment="dawn | geo | app"
    )
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True, unique=True)
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ── Relevance scoring ────────────────────────────────────
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    keyword_score: Mapped[float] = mapped_column(Float, default=0.0)
    semantic_score: Mapped[float] = mapped_column(Float, default=0.0)
    recency_score: Mapped[float] = mapped_column(Float, default=0.0)
    category_score: Mapped[float] = mapped_column(Float, default=0.0)

    # ── MCQ generation ───────────────────────────────────────
    mcq_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    mcq_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    mcq_options: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment='{"a":"...","b":"...","c":"...","d":"..."}'
    )
    mcq_correct_answer: Mapped[str | None] = mapped_column(
        String(1), nullable=True, comment="a | b | c | d"
    )
    mcq_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Admin workflow ───────────────────────────────────────
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_included_in_prediction: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── pgvector: 1536-dim for OpenAI text-embedding-3-small ─
    embedding: Mapped[Any | None] = mapped_column(Vector(1536), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Indexes ──────────────────────────────────────────────
    __table_args__ = (
        Index("ix_ca_published_date", "published_date"),
        Index("ix_ca_relevance_score", "relevance_score"),
        Index("ix_ca_is_included", "is_included_in_prediction"),
        Index("ix_ca_is_approved", "is_approved"),
        Index("ix_ca_source_date", "source_name", "published_date"),
        Index(
            "ix_ca_embedding_hnsw",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<CurrentAffairsItem id={self.id} headline={self.headline!r}>"
