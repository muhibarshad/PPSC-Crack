"""
CurrentAffairsItem — daily news items scored for exam relevance.
Includes pgvector embedding for semantic similarity matching.
"""

import uuid
from datetime import datetime, date
from typing import Any

from sqlalchemy import String, Float, Boolean, Text, Date, DateTime, Index, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, Vector


class CurrentAffairsItem(Base):
    __tablename__ = "current_affairs_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_included_in_prediction: Mapped[bool] = mapped_column(Boolean, default=False)
    mcq_generated: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── pgvector: 1536-dim for OpenAI text-embedding-3-small ─
    embedding: Mapped[Any | None] = mapped_column(Vector(1536), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Indexes ──────────────────────────────────────────────
    __table_args__ = (
        Index("ix_ca_published_date", "published_date"),
        Index("ix_ca_relevance_score", "relevance_score"),
        Index("ix_ca_is_included", "is_included_in_prediction"),
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
