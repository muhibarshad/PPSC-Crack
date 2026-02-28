"""add predictions table

Revision ID: 002_predictions
Revises: 001_initial_schema
Create Date: 2026-02-28

Creates the predictions table for AI-generated exam predictions.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "002_predictions"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("job_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("prediction_date", sa.Date(), nullable=False, comment="Target exam month/date"),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("include_current_affairs", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("questions_json", sa.JSON(), nullable=True, comment="Full array of predicted MCQs"),
        sa.Column("current_affairs_json", sa.JSON(), nullable=True, comment="Current affairs MCQs section"),
        sa.Column("topic_distribution", sa.JSON(), nullable=True, comment="Topic → question count allocation"),
        sa.Column("generation_metadata", sa.JSON(), nullable=True, comment="Weights, algorithm params, etc."),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("paper_count_basis", sa.Integer(), nullable=False, server_default="0", comment="Number of past papers used"),
        sa.Column("pattern_consistency", sa.Float(), nullable=False, server_default="0.0", comment="0.0-1.0 topic pattern stability"),
        sa.Column("status", sa.String(50), nullable=False, server_default="generating", comment="generating|completed|failed|published"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["job_type_id"], ["job_types.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["pattern_snapshots.id"], ondelete="SET NULL"),
    )

    # Indexes
    op.create_index("ix_pred_job_type_id", "predictions", ["job_type_id"])
    op.create_index("ix_pred_prediction_date", "predictions", ["prediction_date"])
    op.create_index("ix_pred_status", "predictions", ["status"])
    op.create_index("ix_pred_is_published", "predictions", ["is_published"])
    op.create_index("ix_pred_job_date", "predictions", ["job_type_id", "prediction_date"])


def downgrade() -> None:
    op.drop_index("ix_pred_job_date", table_name="predictions")
    op.drop_index("ix_pred_is_published", table_name="predictions")
    op.drop_index("ix_pred_status", table_name="predictions")
    op.drop_index("ix_pred_prediction_date", table_name="predictions")
    op.drop_index("ix_pred_job_type_id", table_name="predictions")
    op.drop_table("predictions")
