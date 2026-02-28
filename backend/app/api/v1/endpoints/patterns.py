"""
Patterns endpoint — GET /api/v1/patterns/overview/{job_type_id}
================================================================
Returns the current pattern-intelligence state for a job type.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.dependencies import DBSession
from app.models.job_type import JobType
from app.models.paper import Paper
from app.models.pattern_snapshot import PatternSnapshot
from app.models.question import Question
from app.models.topic import Topic
from app.models.topic_frequency import TopicFrequencyByJob
from app.schemas.pattern_overview import (
    DueTopic,
    HighFrequencyFact,
    PatternOverviewResponse,
    RepeatQuestionSummary,
    TopicTrend,
)

logger = logging.getLogger(__name__)

router = APIRouter()

DUE_TOPIC_ABSENCE = 3


@router.get(
    "/overview/{job_type_id}",
    response_model=PatternOverviewResponse,
    summary="Get current pattern intelligence for a job type",
)
async def get_pattern_overview(job_type_id: UUID, db: DBSession):
    """Return topic trends, due topics, high-freq facts, and repeat-question
    summary for the given job type. Pulls from the latest pattern snapshot
    and live DB aggregations.
    """
    # Validate job type exists
    job_type = await db.get(JobType, job_type_id)
    if not job_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job type {job_type_id} not found",
        )

    # ── Latest snapshot ──────────────────────────────────────
    snapshot_q = (
        select(PatternSnapshot)
        .where(PatternSnapshot.job_type_id == job_type_id)
        .order_by(PatternSnapshot.created_at.desc())
        .limit(1)
    )
    snapshot = (await db.execute(snapshot_q)).scalar_one_or_none()

    # ── Paper count ──────────────────────────────────────────
    paper_count_q = (
        select(func.count(Paper.id))
        .where(Paper.job_type_id == job_type_id, Paper.ingestion_status == "completed")
    )
    paper_count = (await db.execute(paper_count_q)).scalar() or 0

    # ── Topic trends (from latest year frequency + topic trend_direction) ─
    latest_year_q = (
        select(func.max(TopicFrequencyByJob.year))
        .where(TopicFrequencyByJob.job_type_id == job_type_id)
    )
    latest_year = (await db.execute(latest_year_q)).scalar()

    topic_trends: list[TopicTrend] = []
    if latest_year:
        freq_q = (
            select(TopicFrequencyByJob, Topic)
            .join(Topic, TopicFrequencyByJob.topic_id == Topic.id)
            .where(
                TopicFrequencyByJob.job_type_id == job_type_id,
                TopicFrequencyByJob.year == latest_year,
            )
            .order_by(TopicFrequencyByJob.percentage_of_paper.desc())
        )
        freq_rows = (await db.execute(freq_q)).all()

        for row in freq_rows:
            tf = row[0]  # TopicFrequencyByJob
            topic = row[1]  # Topic
            topic_trends.append(TopicTrend(
                topic_id=topic.id,
                topic_name=topic.name,
                display_name=topic.display_name,
                percentage=tf.percentage_of_paper,
                question_count=tf.question_count,
                trend_direction=topic.trend_direction,
            ))

    # ── Due topics ───────────────────────────────────────────
    due_topics: list[DueTopic] = []
    if snapshot and snapshot.high_probability_facts:
        raw_due = snapshot.high_probability_facts.get("due_topics", [])
        for dt in raw_due:
            due_topics.append(DueTopic(
                topic_id=UUID(dt["topic_id"]) if isinstance(dt["topic_id"], str) else dt["topic_id"],
                topic_name=dt["topic_name"],
                display_name=dt["display_name"],
                absent_papers=dt.get("absent_papers", DUE_TOPIC_ABSENCE),
            ))

    # ── High-frequency facts ─────────────────────────────────
    high_freq_facts: list[HighFrequencyFact] = []
    if snapshot and snapshot.high_probability_facts:
        raw_facts = snapshot.high_probability_facts.get("facts", [])
        for f in raw_facts:
            high_freq_facts.append(HighFrequencyFact(
                fact=f["fact"],
                paper_count=f["paper_count"],
                total_appearances=f["total_appearances"],
            ))

    # ── Repeat-question summary ──────────────────────────────
    paper_ids_q = (
        select(Paper.id)
        .where(Paper.job_type_id == job_type_id, Paper.ingestion_status == "completed")
    )
    paper_ids = [r for (r,) in (await db.execute(paper_ids_q)).all()]

    repeat_groups = 0
    repeat_total = 0
    if paper_ids:
        groups_q = (
            select(func.count(func.distinct(Question.similarity_group_id)))
            .where(
                Question.paper_id.in_(paper_ids),
                Question.is_repeated.is_(True),
                Question.similarity_group_id.isnot(None),
            )
        )
        repeat_groups = (await db.execute(groups_q)).scalar() or 0

        total_q = (
            select(func.count(Question.id))
            .where(
                Question.paper_id.in_(paper_ids),
                Question.is_repeated.is_(True),
            )
        )
        repeat_total = (await db.execute(total_q)).scalar() or 0

    return PatternOverviewResponse(
        job_type_id=job_type_id,
        job_type_name=job_type.name,
        snapshot_date=snapshot.snapshot_date if snapshot else None,
        paper_count=paper_count,
        confidence_score=snapshot.confidence_score if snapshot else 0.0,
        topic_trends=topic_trends,
        due_topics=due_topics,
        high_frequency_facts=high_freq_facts,
        repeat_summary=RepeatQuestionSummary(
            total_groups=repeat_groups,
            total_repeated_questions=repeat_total,
        ),
        predicted_topic_ratios=snapshot.predicted_topic_ratios if snapshot else None,
        snapshot_id=snapshot.id if snapshot else None,
        snapshot_created_at=snapshot.created_at if snapshot else None,
    )
