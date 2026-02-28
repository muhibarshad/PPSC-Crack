"""
Dashboard API — Student home page data
========================================
GET /api/v1/dashboard/home  →  aggregated dashboard payload.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.dependencies import DBSession, get_current_user
from app.models.job_type import JobType
from app.models.prediction import Prediction
from app.models.topic import Topic
from app.models.topic_frequency import TopicFrequencyByJob
from app.models.user import User
from app.schemas.dashboard import (
    DashboardHomeResponse,
    LatestPredictedPaper,
    NextStoryToRead,
    ProgressRingData,
    QuickStats,
    StreakData,
    TodaysFocusTopic,
)

logger = logging.getLogger(__name__)

router = APIRouter()

WORDS_PER_MINUTE = 200


async def _get_progress(
    db: DBSession, user: User, job_type_ids: list[UUID],
) -> ProgressRingData:
    """Compute readiness % — topics with stories read / total topics for jobs."""
    if not job_type_ids:
        return ProgressRingData()

    # Count distinct topics across selected jobs
    total_q = (
        select(func.count(func.distinct(TopicFrequencyByJob.topic_id)))
        .where(TopicFrequencyByJob.job_type_id.in_(job_type_ids))
    )
    total = (await db.execute(total_q)).scalar() or 0

    # "Completed" = topics the student has marked in learning_progress
    progress = user.learning_progress or {}
    completed_ids = [
        k for k, v in progress.items()
        if isinstance(v, dict) and v.get("completed")
    ]
    completed = len(completed_ids)

    pct = round((completed / total) * 100, 1) if total > 0 else 0.0

    return ProgressRingData(
        topics_completed=completed,
        topics_total=total,
        readiness_percent=pct,
    )


async def _get_streak(user: User) -> StreakData:
    """Calculate streak from learning_progress session dates."""
    progress = user.learning_progress or {}
    sessions: list[str] = progress.get("session_dates", [])

    if not sessions:
        return StreakData()

    today = datetime.now(timezone.utc).date()

    # Parse and deduplicate dates
    dates = set()
    for s in sessions:
        try:
            dates.add(datetime.fromisoformat(s).date() if "T" in s else datetime.strptime(s, "%Y-%m-%d").date())
        except (ValueError, TypeError):
            continue

    sorted_dates = sorted(dates, reverse=True)

    studied_today = today in dates

    # Count current streak going backwards from today
    current = 0
    check = today
    for d in sorted_dates:
        if d == check:
            current += 1
            check -= timedelta(days=1)
        elif d < check:
            break

    # Longest streak
    longest = 0
    streak = 0
    prev = None
    for d in sorted(dates):
        if prev and (d - prev).days == 1:
            streak += 1
        else:
            streak = 1
        longest = max(longest, streak)
        prev = d

    return StreakData(
        current_streak=current,
        longest_streak=longest,
        studied_today=studied_today,
    )


async def _get_todays_focus(
    db: DBSession, job_type_ids: list[UUID],
) -> TodaysFocusTopic | None:
    """Highest-weight topic across selected job types."""
    if not job_type_ids:
        return None

    # Latest year for any selected job
    latest_year_q = (
        select(func.max(TopicFrequencyByJob.year))
        .where(TopicFrequencyByJob.job_type_id.in_(job_type_ids))
    )
    latest_year = (await db.execute(latest_year_q)).scalar()
    if not latest_year:
        return None

    # Sum percentages across jobs, pick the top one
    agg_q = (
        select(
            TopicFrequencyByJob.topic_id,
            func.sum(TopicFrequencyByJob.percentage_of_paper).label("total_pct"),
        )
        .where(
            TopicFrequencyByJob.job_type_id.in_(job_type_ids),
            TopicFrequencyByJob.year == latest_year,
        )
        .group_by(TopicFrequencyByJob.topic_id)
        .order_by(func.sum(TopicFrequencyByJob.percentage_of_paper).desc())
        .limit(1)
    )
    row = (await db.execute(agg_q)).first()
    if not row:
        return None

    topic = await db.get(Topic, row.topic_id)
    if not topic:
        return None

    return TodaysFocusTopic(
        topic_id=topic.id,
        topic_name=topic.name,
        display_name=topic.display_name,
        percentage=round(float(row.total_pct), 1),
        trend_direction=topic.trend_direction,
        icon=topic.icon,
    )


async def _get_latest_prediction(
    db: DBSession, job_type_ids: list[UUID], is_premium: bool,
) -> LatestPredictedPaper | None:
    """Most recently published prediction for the student's jobs (premium only)."""
    if not is_premium or not job_type_ids:
        return None

    q = (
        select(Prediction)
        .where(
            Prediction.is_published.is_(True),
            Prediction.job_type_id.in_(job_type_ids),
        )
        .order_by(Prediction.published_at.desc())
        .limit(1)
    )
    pred = (await db.execute(q)).scalar_one_or_none()
    if not pred:
        return None

    jt = await db.get(JobType, pred.job_type_id)

    return LatestPredictedPaper(
        prediction_id=pred.id,
        title=pred.title,
        prediction_date=pred.prediction_date,
        confidence_score=pred.confidence_score,
        total_questions=pred.total_questions,
        job_type_name=jt.name if jt else "",
    )


async def _get_next_story(
    db: DBSession, job_type_ids: list[UUID], user: User,
) -> NextStoryToRead | None:
    """Find the highest-frequency topic with a story that hasn't been read yet."""
    if not job_type_ids:
        return None

    progress = user.learning_progress or {}
    read_ids_raw = progress.get("stories_read", [])
    read_ids: list[UUID] = []
    for r in read_ids_raw:
        try:
            read_ids.append(UUID(str(r)))
        except (ValueError, TypeError):
            continue

    # Latest year
    latest_year_q = (
        select(func.max(TopicFrequencyByJob.year))
        .where(TopicFrequencyByJob.job_type_id.in_(job_type_ids))
    )
    latest_year = (await db.execute(latest_year_q)).scalar()
    if not latest_year:
        return None

    # Get topics with stories, ordered by frequency, excluding already-read
    q = (
        select(Topic, func.sum(TopicFrequencyByJob.percentage_of_paper).label("pct"))
        .join(TopicFrequencyByJob, TopicFrequencyByJob.topic_id == Topic.id)
        .where(
            TopicFrequencyByJob.job_type_id.in_(job_type_ids),
            TopicFrequencyByJob.year == latest_year,
            Topic.story_document.isnot(None),
            Topic.story_word_count > 0,
        )
    )
    if read_ids:
        q = q.where(Topic.id.notin_(read_ids))

    q = (
        q.group_by(Topic.id)
        .order_by(func.sum(TopicFrequencyByJob.percentage_of_paper).desc())
        .limit(1)
    )
    row = (await db.execute(q)).first()
    if not row:
        return None

    topic: Topic = row[0]
    wc = topic.story_word_count or 0

    return NextStoryToRead(
        topic_id=topic.id,
        topic_name=topic.name,
        display_name=topic.display_name,
        story_word_count=wc,
        estimated_read_minutes=max(1, round(wc / WORDS_PER_MINUTE)) if wc else 0,
        frequency_score=topic.frequency_score,
    )


async def _get_quick_stats(user: User) -> QuickStats:
    """Pull quick stats from user.learning_progress JSON."""
    progress = user.learning_progress or {}
    completed_ids = [
        k for k, v in progress.items()
        if isinstance(v, dict) and v.get("completed")
    ]
    sessions: list[str] = progress.get("session_dates", [])
    unique_days = set()
    for s in sessions:
        try:
            d = datetime.fromisoformat(s).date() if "T" in s else datetime.strptime(s, "%Y-%m-%d").date()
            unique_days.add(d)
        except (ValueError, TypeError):
            continue

    return QuickStats(
        topics_completed=len(completed_ids),
        questions_practiced=progress.get("questions_practiced", 0),
        days_active=len(unique_days),
    )


# ═══════════════════════════════════════════════════════════
# Endpoint
# ═══════════════════════════════════════════════════════════

@router.get(
    "/home",
    response_model=DashboardHomeResponse,
    summary="Get student dashboard home data",
)
async def get_dashboard_home(
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Return all data needed to render the student dashboard home page."""

    job_type_ids: list[UUID] = []
    job_names: list[str] = []

    if current_user.selected_job_types:
        for jt_id in current_user.selected_job_types:
            jt = await db.get(JobType, jt_id)
            if jt:
                job_type_ids.append(jt.id)
                job_names.append(jt.name)

    progress = await _get_progress(db, current_user, job_type_ids)
    streak = await _get_streak(current_user)
    todays_focus = await _get_todays_focus(db, job_type_ids)
    latest_pred = await _get_latest_prediction(db, job_type_ids, current_user.is_premium)
    next_story = await _get_next_story(db, job_type_ids, current_user)
    quick_stats = await _get_quick_stats(current_user)

    return DashboardHomeResponse(
        greeting_name=current_user.name.split()[0] if current_user.name else "Student",
        subscription_tier=current_user.subscription_tier,
        is_premium=current_user.is_premium,
        progress=progress,
        streak=streak,
        quick_stats=quick_stats,
        todays_focus=todays_focus,
        latest_prediction=latest_pred,
        next_story=next_story,
        selected_job_names=job_names,
    )
