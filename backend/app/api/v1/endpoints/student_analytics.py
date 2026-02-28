"""
Student Analytics API — GET /api/v1/student/analytics
======================================================
Returns all data needed to render the /dashboard/analytics page:
  1. Study Streak Calendar (90 days)
  2. Topic Completion Bars
  3. Quiz Score Trend
  4. Exam Readiness Score (weighted by topic frequency)
  5. Time Studied Per Day (30 days)
  6. Comparison — user vs average peer readiness
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta, date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DBSession, get_current_user
from app.models.topic import Topic
from app.models.topic_frequency import TopicFrequencyByJob
from app.models.user import User
from app.schemas.student_analytics import (
    DailyStudyMinutes,
    ExamReadiness,
    QuizScorePoint,
    ReadinessComparison,
    StudentAnalyticsResponse,
    StudyDay,
    TopicCompletion,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── helpers ────────────────────────────────────────────────

def _parse_date(s: str) -> date | None:
    """Safely parse a date string from learning_progress."""
    try:
        if "T" in s:
            return datetime.fromisoformat(s).date()
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _parse_minutes_map(progress: dict) -> dict[date, int]:
    """
    Extract {date: minutes_studied} from learning_progress JSON.
    Expected key: ``study_minutes`` → list of {"date": "...", "minutes": N}
    Falls back to counting session_dates (1 session ≈ 30 min).
    """
    minutes_map: dict[date, int] = {}

    # Primary: explicit study_minutes entries
    for entry in progress.get("study_minutes", []):
        d = _parse_date(entry.get("date", ""))
        if d:
            minutes_map[d] = minutes_map.get(d, 0) + int(entry.get("minutes", 0))

    # Fallback: count session_dates as 30-min blocks
    if not minutes_map:
        for s in progress.get("session_dates", []):
            d = _parse_date(s)
            if d:
                minutes_map[d] = minutes_map.get(d, 0) + 30

    return minutes_map


def _parse_quiz_scores(progress: dict) -> list[QuizScorePoint]:
    """
    Extract quiz score data from learning_progress JSON.
    Expected key: ``quiz_results`` → list of {"date": "...", "score_percent": N, "total": N}
    Falls back to ``practice_results`` with same structure.
    """
    results: list[QuizScorePoint] = []
    raw = progress.get("quiz_results", progress.get("practice_results", []))
    for entry in raw:
        d = _parse_date(entry.get("date", ""))
        if d:
            results.append(QuizScorePoint(
                date=d,
                score_percent=float(entry.get("score_percent", 0)),
                total_questions=int(entry.get("total", 0)),
            ))
    results.sort(key=lambda x: x.date)
    return results


# ─── 1. Study Streak Calendar (90 days) ─────────────────────

def _build_study_calendar(progress: dict) -> list[StudyDay]:
    """GitHub-style heatmap for the past 90 days."""
    minutes_map = _parse_minutes_map(progress)
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=89)

    calendar: list[StudyDay] = []
    for offset in range(90):
        d = start + timedelta(days=offset)
        calendar.append(StudyDay(date=d, minutes_studied=minutes_map.get(d, 0)))
    return calendar


# ─── 2. Topic Completion Bars ────────────────────────────────

async def _build_topic_completions(
    db: AsyncSession,
    user: User,
    job_type_ids: list[UUID],
) -> list[TopicCompletion]:
    """% completion per topic across selected jobs."""
    if not job_type_ids:
        return []

    # Get latest year
    latest_year = (await db.execute(
        select(func.max(TopicFrequencyByJob.year))
        .where(TopicFrequencyByJob.job_type_id.in_(job_type_ids))
    )).scalar()
    if not latest_year:
        return []

    # Aggregate frequency weight per topic
    q = (
        select(
            Topic.id,
            Topic.name,
            Topic.display_name,
            func.sum(TopicFrequencyByJob.percentage_of_paper).label("weight"),
        )
        .join(TopicFrequencyByJob, TopicFrequencyByJob.topic_id == Topic.id)
        .where(
            TopicFrequencyByJob.job_type_id.in_(job_type_ids),
            TopicFrequencyByJob.year == latest_year,
        )
        .group_by(Topic.id)
        .order_by(func.sum(TopicFrequencyByJob.percentage_of_paper).desc())
    )
    rows = (await db.execute(q)).all()

    progress = user.learning_progress or {}
    completions: list[TopicCompletion] = []

    for row in rows:
        topic_id, name, display, weight = row
        topic_data = progress.get(str(topic_id), {})
        completed = isinstance(topic_data, dict) and topic_data.get("completed", False)
        completions.append(TopicCompletion(
            topic_id=topic_id,
            topic_name=name,
            display_name=display,
            completed=completed,
            weight=round(float(weight), 2),
            completion_percent=100.0 if completed else 0.0,
        ))

    return completions


# ─── 4. Exam Readiness Score (weighted) ─────────────────────

async def _compute_readiness(
    db: AsyncSession,
    user: User,
    job_type_ids: list[UUID],
) -> ExamReadiness:
    """
    Formula: (completed_topic_weight / total_topic_weight) × 100
    Weight = sum(percentage_of_paper) for each topic in latest year.
    """
    if not job_type_ids:
        return ExamReadiness()

    latest_year = (await db.execute(
        select(func.max(TopicFrequencyByJob.year))
        .where(TopicFrequencyByJob.job_type_id.in_(job_type_ids))
    )).scalar()
    if not latest_year:
        return ExamReadiness()

    q = (
        select(
            TopicFrequencyByJob.topic_id,
            func.sum(TopicFrequencyByJob.percentage_of_paper).label("weight"),
        )
        .where(
            TopicFrequencyByJob.job_type_id.in_(job_type_ids),
            TopicFrequencyByJob.year == latest_year,
        )
        .group_by(TopicFrequencyByJob.topic_id)
    )
    rows = (await db.execute(q)).all()

    progress = user.learning_progress or {}
    total_weight = 0.0
    completed_weight = 0.0
    total_topics = 0
    completed_topics = 0

    for topic_id, weight in rows:
        w = float(weight)
        total_weight += w
        total_topics += 1

        topic_data = progress.get(str(topic_id), {})
        if isinstance(topic_data, dict) and topic_data.get("completed"):
            completed_weight += w
            completed_topics += 1

    pct = round((completed_weight / total_weight) * 100, 1) if total_weight > 0 else 0.0

    return ExamReadiness(
        readiness_percent=pct,
        completed_weight=round(completed_weight, 2),
        total_weight=round(total_weight, 2),
        topics_completed=completed_topics,
        topics_total=total_topics,
    )


# ─── 5. Time Studied Per Day (30 days) ──────────────────────

def _build_daily_study(progress: dict) -> list[DailyStudyMinutes]:
    """Bar chart data for past 30 days."""
    minutes_map = _parse_minutes_map(progress)
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=29)

    days: list[DailyStudyMinutes] = []
    for offset in range(30):
        d = start + timedelta(days=offset)
        days.append(DailyStudyMinutes(date=d, minutes=minutes_map.get(d, 0)))
    return days


# ─── 6. Comparison — user vs average readiness ──────────────

async def _compute_comparison(
    db: AsyncSession,
    user: User,
    user_readiness: float,
    job_type_ids: list[UUID],
) -> ReadinessComparison:
    """
    Compare user's readiness with the average of all students
    preparing for the same job types.
    """
    if not job_type_ids:
        return ReadinessComparison(user_readiness=user_readiness)

    # Find peer users who share at least one job type
    peers_q = (
        select(User)
        .where(
            User.role == "student",
            User.id != user.id,
            User.selected_job_types.isnot(None),
        )
    )
    result = await db.execute(peers_q)
    peers = result.scalars().all()

    # Get latest year
    latest_year = (await db.execute(
        select(func.max(TopicFrequencyByJob.year))
        .where(TopicFrequencyByJob.job_type_id.in_(job_type_ids))
    )).scalar()

    if not latest_year:
        return ReadinessComparison(user_readiness=user_readiness)

    # Pre-fetch topic weights
    weight_q = (
        select(
            TopicFrequencyByJob.topic_id,
            func.sum(TopicFrequencyByJob.percentage_of_paper).label("weight"),
        )
        .where(
            TopicFrequencyByJob.job_type_id.in_(job_type_ids),
            TopicFrequencyByJob.year == latest_year,
        )
        .group_by(TopicFrequencyByJob.topic_id)
    )
    weight_rows = (await db.execute(weight_q)).all()
    topic_weights = {str(tid): float(w) for tid, w in weight_rows}
    total_weight = sum(topic_weights.values())

    if total_weight == 0:
        return ReadinessComparison(user_readiness=user_readiness)

    # Compute average readiness of peers with overlapping jobs
    peer_readiness_values: list[float] = []
    job_set = set(str(j) for j in job_type_ids)

    for peer in peers:
        peer_jobs = peer.selected_job_types or []
        peer_job_set = set(str(j) for j in peer_jobs)
        if not peer_job_set.intersection(job_set):
            continue

        peer_progress = peer.learning_progress or {}
        peer_completed_w = 0.0
        for tid, w in topic_weights.items():
            td = peer_progress.get(tid, {})
            if isinstance(td, dict) and td.get("completed"):
                peer_completed_w += w

        peer_pct = (peer_completed_w / total_weight) * 100
        peer_readiness_values.append(peer_pct)

    avg = round(sum(peer_readiness_values) / len(peer_readiness_values), 1) if peer_readiness_values else 0.0

    return ReadinessComparison(
        user_readiness=round(user_readiness, 1),
        average_readiness=avg,
        total_peers=len(peer_readiness_values),
    )


# ═══════════════════════════════════════════════════════════
# Endpoint
# ═══════════════════════════════════════════════════════════

@router.get(
    "/analytics",
    response_model=StudentAnalyticsResponse,
    summary="Get student analytics data",
)
async def get_student_analytics(
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Return all data needed to render the student analytics page."""

    job_type_ids: list[UUID] = []
    if current_user.selected_job_types:
        job_type_ids = [UUID(str(jt)) for jt in current_user.selected_job_types]

    progress = current_user.learning_progress or {}

    # Build all sections
    study_calendar = _build_study_calendar(progress)
    topic_completions = await _build_topic_completions(db, current_user, job_type_ids)
    quiz_scores = _parse_quiz_scores(progress)
    readiness = await _compute_readiness(db, current_user, job_type_ids)
    daily_study = _build_daily_study(progress)
    comparison = await _compute_comparison(
        db, current_user, readiness.readiness_percent, job_type_ids
    )

    return StudentAnalyticsResponse(
        study_calendar=study_calendar,
        topic_completions=topic_completions,
        quiz_scores=quiz_scores,
        readiness=readiness,
        daily_study_minutes=daily_study,
        comparison=comparison,
    )
