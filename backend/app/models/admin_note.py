"""
AdminNote — raw admin-contributed content that gets processed into story documents.
Includes pgvector embedding for content matching.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Integer, Boolean, Text, String, DateTime, ForeignKey, Index, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, Vector


class AdminNote(Base):
    __tablename__ = "admin_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    processed_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    position_in_story: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── pgvector: 1536-dim for content matching ──────────────
    embedding: Mapped[Any | None] = mapped_column(Vector(1536), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Relationships ──────────────────────────────────────
    topic_rel = relationship("Topic", back_populates="admin_notes", lazy="selectin")

    # ── Indexes ──────────────────────────────────────────────
    __table_args__ = (
        Index("ix_an_processed", "processed"),
        Index("ix_an_assigned_topic_id", "assigned_topic_id"),
        Index(
            "ix_an_embedding_hnsw",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<AdminNote id={self.id} processed={self.processed}>"
