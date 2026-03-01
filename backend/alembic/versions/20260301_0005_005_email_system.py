"""005_email_system — email_preferences + email_logs tables

Revision ID: 005
Revises: 004
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "005_email_system"
down_revision = "004_add_stripe_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── email_preferences ────────────────────────────────────
    op.create_table(
        "email_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("welcome", sa.Boolean(), nullable=False, server_default=sa.text("true"), comment="Welcome email on registration"),
        sa.Column("subscription_confirmation", sa.Boolean(), nullable=False, server_default=sa.text("true"), comment="Payment / subscription confirmation"),
        sa.Column("subscription_expiry_warning", sa.Boolean(), nullable=False, server_default=sa.text("true"), comment="3-day expiry warning"),
        sa.Column("new_predicted_paper", sa.Boolean(), nullable=False, server_default=sa.text("true"), comment="New predicted paper published"),
        sa.Column("weekly_current_affairs", sa.Boolean(), nullable=False, server_default=sa.text("true"), comment="Monday weekly digest"),
        sa.Column("password_reset", sa.Boolean(), nullable=False, server_default=sa.text("true"), comment="Password reset (always sent, but tracked)"),
        sa.Column("marketing", sa.Boolean(), nullable=False, server_default=sa.text("true"), comment="Promotional / upgrade nudges"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_email_preferences_user"),
    )
    op.create_index("ix_email_preferences_user_id", "email_preferences", ["user_id"])

    # ── email_logs ───────────────────────────────────────────
    op.create_table(
        "email_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_email", sa.String(255), nullable=False),
        sa.Column("email_type", sa.String(50), nullable=False, comment="welcome | subscription_confirmation | subscription_expiry_warning | new_predicted_paper | weekly_current_affairs | password_reset"),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("resend_id", sa.String(255), nullable=True, comment="Resend API message ID"),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'sent'"), comment="sent | failed | bounced"),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_email_logs_user_id", "email_logs", ["user_id"])
    op.create_index("ix_email_logs_to_email", "email_logs", ["to_email"])
    op.create_index("ix_email_logs_email_type", "email_logs", ["email_type"])


def downgrade() -> None:
    op.drop_table("email_logs")
    op.drop_table("email_preferences")
