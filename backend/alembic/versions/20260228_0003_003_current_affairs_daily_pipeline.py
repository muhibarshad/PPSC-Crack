"""003 — Current Affairs daily pipeline: expanded fields for RSS, scoring, MCQ, admin workflow.

Revision ID: 003_current_affairs_daily
Revises: 002_predictions
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = "003_current_affairs_daily"
down_revision = "002_predictions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── New columns on current_affairs_items ──────────────────
    op.add_column("current_affairs_items", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column(
        "current_affairs_items",
        sa.Column("source_name", sa.String(100), nullable=True, comment="dawn | geo | app"),
    )

    # Scoring breakdown
    op.add_column("current_affairs_items", sa.Column("keyword_score", sa.Float(), server_default="0.0", nullable=False))
    op.add_column("current_affairs_items", sa.Column("semantic_score", sa.Float(), server_default="0.0", nullable=False))
    op.add_column("current_affairs_items", sa.Column("recency_score", sa.Float(), server_default="0.0", nullable=False))
    op.add_column("current_affairs_items", sa.Column("category_score", sa.Float(), server_default="0.0", nullable=False))

    # MCQ fields
    op.add_column("current_affairs_items", sa.Column("mcq_text", sa.Text(), nullable=True))
    op.add_column(
        "current_affairs_items",
        sa.Column("mcq_options", JSONB(), nullable=True, comment='{"a":"...","b":"...","c":"...","d":"..."}'),
    )
    op.add_column(
        "current_affairs_items",
        sa.Column("mcq_correct_answer", sa.String(1), nullable=True, comment="a | b | c | d"),
    )
    op.add_column("current_affairs_items", sa.Column("mcq_explanation", sa.Text(), nullable=True))

    # Admin workflow
    op.add_column("current_affairs_items", sa.Column("is_approved", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("current_affairs_items", sa.Column("approved_by", UUID(as_uuid=True), nullable=True))
    op.add_column("current_affairs_items", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "current_affairs_items",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Make source_url unique to prevent duplicate RSS articles
    op.create_unique_constraint("uq_ca_source_url", "current_affairs_items", ["source_url"])

    # New indexes
    op.create_index("ix_ca_source_name", "current_affairs_items", ["source_name"])
    op.create_index("ix_ca_is_approved", "current_affairs_items", ["is_approved"])
    op.create_index("ix_ca_source_date", "current_affairs_items", ["source_name", "published_date"])


def downgrade() -> None:
    op.drop_index("ix_ca_source_date", table_name="current_affairs_items")
    op.drop_index("ix_ca_is_approved", table_name="current_affairs_items")
    op.drop_index("ix_ca_source_name", table_name="current_affairs_items")
    op.drop_constraint("uq_ca_source_url", "current_affairs_items", type_="unique")

    op.drop_column("current_affairs_items", "updated_at")
    op.drop_column("current_affairs_items", "approved_at")
    op.drop_column("current_affairs_items", "approved_by")
    op.drop_column("current_affairs_items", "is_approved")
    op.drop_column("current_affairs_items", "mcq_explanation")
    op.drop_column("current_affairs_items", "mcq_correct_answer")
    op.drop_column("current_affairs_items", "mcq_options")
    op.drop_column("current_affairs_items", "mcq_text")
    op.drop_column("current_affairs_items", "category_score")
    op.drop_column("current_affairs_items", "recency_score")
    op.drop_column("current_affairs_items", "semantic_score")
    op.drop_column("current_affairs_items", "keyword_score")
    op.drop_column("current_affairs_items", "source_name")
    op.drop_column("current_affairs_items", "summary")
