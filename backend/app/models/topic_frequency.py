"""
TopicFrequencyByJob — cross-tabulation of topic appearance per job type per year.
"""

import uuid
from datetime import datetime

from sqlalchemy import Integer, Float, ForeignKey, Index, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TopicFrequencyByJob(Base):
    __tablename__ = "topic_frequency_by_job"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False
    )
    job_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_types.id", ondelete="CASCADE"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    percentage_of_paper: Mapped[float] = mapped_column(Float, default=0.0)

    # ── Relationships ──────────────────────────────────────
    topic_rel = relationship("Topic", back_populates="topic_frequencies", lazy="selectin")
    job_type_rel = relationship("JobType", back_populates="topic_frequencies", lazy="selectin")

    # ── Indexes & Constraints ────────────────────────────────
    __table_args__ = (
        UniqueConstraint("topic_id", "job_type_id", "year", name="uq_topic_job_year"),
        Index("ix_tf_topic_id", "topic_id"),
        Index("ix_tf_job_type_id", "job_type_id"),
        Index("ix_tf_year", "year"),
    )

    def __repr__(self) -> str:
        return f"<TopicFrequencyByJob topic={self.topic_id} job={self.job_type_id} year={self.year}>"
