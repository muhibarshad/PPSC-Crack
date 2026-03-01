"""004 — Add Stripe payment columns to users table

Revision ID: 004_add_stripe_columns
Revises: 20260228_0003_003_current_affairs_daily_pipeline
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa

revision = "004_add_stripe_columns"
down_revision = "003_current_affairs_daily"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "stripe_customer_id",
            sa.String(255),
            unique=True,
            nullable=True,
            comment="Stripe Customer ID — created on first checkout",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "stripe_subscription_id",
            sa.String(255),
            unique=True,
            nullable=True,
            comment="Active Stripe Subscription ID",
        ),
    )
    op.create_index("ix_users_stripe_customer_id", "users", ["stripe_customer_id"])


def downgrade() -> None:
    op.drop_index("ix_users_stripe_customer_id", table_name="users")
    op.drop_column("users", "stripe_subscription_id")
    op.drop_column("users", "stripe_customer_id")
