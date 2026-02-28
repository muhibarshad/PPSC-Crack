"""
Learning-Path API — topic roadmap for a specific job type
==========================================================
GET /api/v1/dashboard/learning-path/{job_type_id}
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select

from app.dependencies import DBSession, get_current_user
from app.models.job_type import JobType
from app.models.topic import Topic
from app.models.topic_frequency import TopicFrequencyByJob
from app.models.user import User
from app.schemas.learning_path import LearningPathResponse, LearningPathTopic

logger = logging.getLogger(__name__)

router = APIRouter()

WORDS_PER_MINUTE = 200
HOT_THRESHOLD_PERCENTILE = 75  # top 25 % of topics → HOT


@router.get(
    "/learning-path/{job_type_id}",
    response_model=LearningPathResponse,
    summary="Get topic roadmap for a job type",
)
async def get_learning_path(
    job_type_id: UUID,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Return all topics for *job_type_id* ordered by predicted exam weight,
    annotated with the current student's progress."""

    # ── Validate job type ────────────────────────────────────
    job_type = await db.get(JobType, job_type_id)
    if not job_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job type {job_type_id} not found",
        )

    # ── Latest frequency year ────────────────────────────────
    latest_year_q = (
        select(func.max(TopicFrequencyByJob.year))
        .where(TopicFrequencyByJob.job_type_id == job_type_id)
    )
    latest_year = (await db.execute(latest_year_q)).scalar()

    if not latest_year:
        return LearningPathResponse(
            job_type_id=job_type.id,
            job_type_name=job_type.name,
        )

    # ── Fetch topics + frequency for this job, latest year ───
    q = (
        select(
            Topic,
            TopicFrequencyByJob.percentage_of_paper.label("pct"),
        )
        .join(TopicFrequencyByJob, TopicFrequencyByJob.topic_id == Topic.id)
        .where(
            TopicFrequencyByJob.job_type_id == job_type_id,
            TopicFrequencyByJob.year == latest_year,
        )
        .order_by(TopicFrequencyByJob.percentage_of_paper.desc())
    )
    rows = (await db.execute(q)).all()

    if not rows:
        return LearningPathResponse(
            job_type_id=job_type.id,
            job_type_name=job_type.name,
        )

    # ── Compute HOT threshold ────────────────────────────────
    percentages = sorted([float(r.pct) for r in rows])
    hot_idx = int(len(percentages) * HOT_THRESHOLD_PERCENTILE / 100)
    hot_cutoff = percentages[hot_idx] if hot_idx < len(percentages) else percentages[-1]

    # ── Student progress from learning_progress JSON ─────────
    progress_map: dict[str, dict] = {}
    lp = current_user.learning_progress or {}
    for key, val in lp.items():
        if isinstance(val, dict):
            progress_map[key] = val

    stories_read: set[str] = set()
    for sid in lp.get("stories_read", []):
        stories_read.add(str(sid))

    # ── Build topic list ─────────────────────────────────────
    topics: list[LearningPathTopic] = []
    completed_count = 0
    in_progress_count = 0

    for rank, row in enumerate(rows, start=1):
        topic: Topic = row[0]
        pct = float(row.pct)
        tid = str(topic.id)

        wc = topic.story_word_count or 0
        has_story = bool(topic.story_document) and wc > 0
        est_min = max(1, round(wc / WORDS_PER_MINUTE)) if wc else 0

        # Determine status
        tp = progress_map.get(tid, {})
        if tp.get("completed"):
            node_status = "completed"
            node_progress = 100.0
            completed_count += 1
        elif tid in stories_read or tp.get("started"):
            node_status = "in-progress"
            node_progress = float(tp.get("progress", 50))
            in_progress_count += 1
        else:
            node_status = "not-started"
            node_progress = 0.0

        topics.append(
            LearningPathTopic(
                topic_id=topic.id,
                topic_name=topic.name,
                display_name=topic.display_name,
                icon=topic.icon,
                color_hex=topic.color_hex,
                frequency_percentage=round(pct, 1),
                trend_direction=topic.trend_direction,
                is_hot=pct >= hot_cutoff,
                story_word_count=wc,
                estimated_read_minutes=est_min,
                has_story=has_story,
                status=node_status,
                progress_percent=node_progress,
                rank=rank,
            )
        )

    total = len(topics)
    overall = round((completed_count / total) * 100, 1) if total else 0.0

    return LearningPathResponse(
        job_type_id=job_type.id,
        job_type_name=job_type.name,
        total_topics=total,
        completed_count=completed_count,
        in_progress_count=in_progress_count,
        overall_percent=overall,
        topics=topics,
    )
