"""initial_schema — complete PPSC Crack database

Revision ID: 001
Revises: —
Create Date: 2026-02-28

Creates all 9 tables with pgvector HNSW indexes:
  - job_types
  - topics
  - papers
  - questions
  - topic_frequency_by_job
  - pattern_snapshots
  - current_affairs_items
  - users
  - admin_notes
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extensions ───────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "unaccent"')

    # ════════════════════════════════════════════════════════
    # 1. job_types
    # ════════════════════════════════════════════════════════
    op.create_table(
        "job_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("department", sa.String(200), nullable=True),
        sa.Column("total_papers", sa.Integer(), server_default="0"),
        sa.Column("avg_questions_per_paper", sa.Float(), server_default="0.0"),
        sa.Column("topic_ratios", postgresql.JSON(), nullable=True),
        sa.Column("last_updated_ratios", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_job_types_slug", "job_types", ["slug"])

    # ════════════════════════════════════════════════════════
    # 2. topics
    # ════════════════════════════════════════════════════════
    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("total_questions", sa.Integer(), server_default="0"),
        sa.Column("last_appeared_date", sa.Date(), nullable=True),
        sa.Column("first_appeared_date", sa.Date(), nullable=True),
        sa.Column("frequency_score", sa.Float(), server_default="0.0"),
        sa.Column("trend_direction", sa.String(20), nullable=True, comment="up | down | stable | new"),
        sa.Column("story_document", sa.Text(), nullable=True),
        sa.Column("story_last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("story_word_count", sa.Integer(), server_default="0"),
        sa.Column("color_hex", sa.String(7), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("parent_topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_topics_name", "topics", ["name"])
    op.create_index("ix_topics_frequency_score", "topics", ["frequency_score"])

    # ════════════════════════════════════════════════════════
    # 3. papers
    # ════════════════════════════════════════════════════════
    op.create_table(
        "papers",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("job_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_types.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paper_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paper_year", sa.Integer(), nullable=False),
        sa.Column("paper_month", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("total_questions", sa.Integer(), server_default="0"),
        sa.Column("ingestion_status", sa.String(50), server_default="'pending'", comment="pending | processing | completed | failed"),
        sa.Column("raw_scan_data", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_papers_job_type_year", "papers", ["job_type_id", "paper_year"])
    op.create_index("ix_papers_ingestion_status", "papers", ["ingestion_status"])

    # ════════════════════════════════════════════════════════
    # 4. questions
    # ════════════════════════════════════════════════════════
    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_number", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("option_a", sa.Text(), nullable=True),
        sa.Column("option_b", sa.Text(), nullable=True),
        sa.Column("option_c", sa.Text(), nullable=True),
        sa.Column("option_d", sa.Text(), nullable=True),
        sa.Column("correct_answer", sa.String(1), nullable=True, comment="a | b | c | d"),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subtopic", sa.String(200), nullable=True),
        sa.Column("difficulty_score", sa.Float(), server_default="0.5", comment="0.0 = easy, 1.0 = hard"),
        sa.Column("fact_extracted", sa.Text(), nullable=True),
        sa.Column("year_appeared", sa.Integer(), nullable=True),
        sa.Column("is_repeated", sa.Boolean(), server_default="false"),
        sa.Column("repeat_count", sa.Integer(), server_default="0"),
        sa.Column("similarity_group_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("needs_review", sa.Boolean(), server_default="true"),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Standard indexes
    op.create_index("ix_questions_paper_id", "questions", ["paper_id"])
    op.create_index("ix_questions_topic_id", "questions", ["topic_id"])
    op.create_index("ix_questions_is_repeated", "questions", ["is_repeated"])
    op.create_index("ix_questions_needs_review", "questions", ["needs_review"])
    op.create_index("ix_questions_year_appeared", "questions", ["year_appeared"])
    op.create_index("ix_questions_similarity_group", "questions", ["similarity_group_id"])

    # pgvector embedding column — added via raw SQL (Alembic doesn't natively understand vector type)
    op.execute("ALTER TABLE questions ADD COLUMN embedding vector(1536)")

    # HNSW index for cosine similarity on questions
    op.execute("""
        CREATE INDEX ix_questions_embedding_hnsw
        ON questions
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # ════════════════════════════════════════════════════════
    # 5. topic_frequency_by_job
    # ════════════════════════════════════════════════════════
    op.create_table(
        "topic_frequency_by_job",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_types.id", ondelete="CASCADE"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("question_count", sa.Integer(), server_default="0"),
        sa.Column("percentage_of_paper", sa.Float(), server_default="0.0"),
        sa.UniqueConstraint("topic_id", "job_type_id", "year", name="uq_topic_job_year"),
    )
    op.create_index("ix_tf_topic_id", "topic_frequency_by_job", ["topic_id"])
    op.create_index("ix_tf_job_type_id", "topic_frequency_by_job", ["job_type_id"])
    op.create_index("ix_tf_year", "topic_frequency_by_job", ["year"])

    # ════════════════════════════════════════════════════════
    # 6. pattern_snapshots
    # ════════════════════════════════════════════════════════
    op.create_table(
        "pattern_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("job_type_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_types.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("paper_count_at_snapshot", sa.Integer(), server_default="0"),
        sa.Column("predicted_topic_ratios", postgresql.JSON(), nullable=True),
        sa.Column("confidence_score", sa.Float(), server_default="0.0"),
        sa.Column("high_probability_facts", postgresql.JSON(), nullable=True),
        sa.Column("current_affairs_patterns", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ps_job_type_id", "pattern_snapshots", ["job_type_id"])
    op.create_index("ix_ps_snapshot_date", "pattern_snapshots", ["snapshot_date"])
    op.create_index("ix_ps_job_date", "pattern_snapshots", ["job_type_id", "snapshot_date"])

    # ════════════════════════════════════════════════════════
    # 7. current_affairs_items
    # ════════════════════════════════════════════════════════
    op.create_table(
        "current_affairs_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("headline", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("published_date", sa.Date(), nullable=True),
        sa.Column("relevance_score", sa.Float(), server_default="0.0"),
        sa.Column("is_included_in_prediction", sa.Boolean(), server_default="false"),
        sa.Column("mcq_generated", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ca_category", "current_affairs_items", ["category"])
    op.create_index("ix_ca_published_date", "current_affairs_items", ["published_date"])
    op.create_index("ix_ca_relevance_score", "current_affairs_items", ["relevance_score"])
    op.create_index("ix_ca_is_included", "current_affairs_items", ["is_included_in_prediction"])

    # pgvector embedding column
    op.execute("ALTER TABLE current_affairs_items ADD COLUMN embedding vector(1536)")

    # HNSW index for cosine similarity on current_affairs_items
    op.execute("""
        CREATE INDEX ix_ca_embedding_hnsw
        ON current_affairs_items
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # ════════════════════════════════════════════════════════
    # 8. users
    # ════════════════════════════════════════════════════════
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), server_default="'user'", comment="user | admin | moderator"),
        sa.Column("is_premium", sa.Boolean(), server_default="false"),
        sa.Column("subscription_tier", sa.String(20), server_default="'free'", comment="free | pro | elite"),
        sa.Column("subscription_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("selected_job_types", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column("learning_progress", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_subscription_tier", "users", ["subscription_tier"])

    # ════════════════════════════════════════════════════════
    # 9. admin_notes
    # ════════════════════════════════════════════════════════
    op.create_table(
        "admin_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("processed", sa.Boolean(), server_default="false"),
        sa.Column("assigned_topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("processed_content", sa.Text(), nullable=True),
        sa.Column("position_in_story", sa.Integer(), nullable=True),
        sa.Column("source_description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_an_processed", "admin_notes", ["processed"])
    op.create_index("ix_an_assigned_topic_id", "admin_notes", ["assigned_topic_id"])

    # pgvector embedding column
    op.execute("ALTER TABLE admin_notes ADD COLUMN embedding vector(1536)")

    # HNSW index for cosine similarity on admin_notes
    op.execute("""
        CREATE INDEX ix_an_embedding_hnsw
        ON admin_notes
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    op.drop_table("admin_notes")
    op.drop_table("users")
    op.drop_table("current_affairs_items")
    op.drop_table("pattern_snapshots")
    op.drop_table("topic_frequency_by_job")
    op.drop_table("questions")
    op.drop_table("papers")
    op.drop_table("topics")
    op.drop_table("job_types")
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
    op.execute('DROP EXTENSION IF EXISTS "unaccent"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
