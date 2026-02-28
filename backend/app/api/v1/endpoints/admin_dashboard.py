"""
Admin Dashboard Endpoints
==========================
GET /api/v1/admin/dashboard  →  aggregated admin dashboard payload.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.dependencies import DBSession, require_admin
from app.models.job_type import JobType
from app.models.paper import Paper
from app.models.pattern_snapshot import PatternSnapshot
from app.models.question import Question
from app.models.topic import Topic
from app.models.user import User
from app.schemas.admin_dashboard import (
    AdminDashboardResponse,
    AdminStatsResponse,
    PredictionHealthItem,
    RecentActivityItem,
    TimelinePaperPoint,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=AdminDashboardResponse,
    summary="Admin dashboard home — stats, timeline, health, activity",
)
async def get_admin_dashboard(
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Return all data needed to render the admin dashboard home screen."""

    # ── 1. Stat Cards ──────────────────────────────────────────
    total_papers = (
        await db.execute(
            select(func.count(Paper.id)).where(
                Paper.ingestion_status == "completed"
            )
        )
    ).scalar() or 0

    total_questions = (
        await db.execute(select(func.count(Question.id)))
    ).scalar() or 0

    topics_discovered = (
        await db.execute(select(func.count(Topic.id)))
    ).scalar() or 0

    avg_confidence = (
        await db.execute(select(func.avg(PatternSnapshot.confidence_score)))
    ).scalar() or 0.0

    stats = AdminStatsResponse(
        total_papers=total_papers,
        total_questions=total_questions,
        topics_discovered=topics_discovered,
        avg_confidence_score=round(float(avg_confidence), 2),
    )

    # ── 2. Timeline — all papers with job type info ──────────
    timeline_q = (
        select(Paper, JobType.name, JobType.slug)
        .join(JobType, Paper.job_type_id == JobType.id)
        .order_by(Paper.paper_year.asc(), Paper.paper_month.asc())
    )
    timeline_rows = (await db.execute(timeline_q)).all()
    timeline = [
        TimelinePaperPoint(
            id=p.id,
            title=p.title,
            paper_year=p.paper_year,
            paper_month=p.paper_month,
            total_questions=p.total_questions,
            ingestion_status=p.ingestion_status,
            job_type_name=jt_name,
            job_type_slug=jt_slug,
            created_at=p.created_at,
        )
        for p, jt_name, jt_slug in timeline_rows
    ]

    # ── 3. Prediction Health — paper count per job type ──────
    jt_health_q = (
        select(
            JobType.id,
            JobType.name,
            JobType.slug,
            func.count(Paper.id).label("paper_count"),
        )
        .outerjoin(
            Paper,
            (Paper.job_type_id == JobType.id)
            & (Paper.ingestion_status == "completed"),
        )
        .where(JobType.is_active == True)  # noqa: E712
        .group_by(JobType.id, JobType.name, JobType.slug)
        .order_by(func.count(Paper.id).desc())
    )
    jt_rows = (await db.execute(jt_health_q)).all()

    # Get latest confidence per job type from snapshots
    latest_confidence: dict[str, float] = {}
    for jt_id, jt_name, jt_slug, pc in jt_rows:
        snap_q = (
            select(PatternSnapshot.confidence_score)
            .where(PatternSnapshot.job_type_id == jt_id)
            .order_by(PatternSnapshot.created_at.desc())
            .limit(1)
        )
        conf = (await db.execute(snap_q)).scalar() or 0.0
        latest_confidence[str(jt_id)] = round(float(conf), 2)

    prediction_health = [
        PredictionHealthItem(
            job_type_id=jt_id,
            job_type_name=jt_name,
            job_type_slug=jt_slug,
            paper_count=pc,
            health="green" if pc >= 50 else ("orange" if pc >= 10 else "blue"),
            confidence_score=latest_confidence.get(str(jt_id), 0.0),
        )
        for jt_id, jt_name, jt_slug, pc in jt_rows
    ]

    # ── 4. Recent Activity — last 5 papers ───────────────────
    recent_q = (
        select(Paper, JobType.name)
        .join(JobType, Paper.job_type_id == JobType.id)
        .order_by(Paper.created_at.desc())
        .limit(5)
    )
    recent_rows = (await db.execute(recent_q)).all()
    recent_activity = [
        RecentActivityItem(
            paper_id=p.id,
            title=p.title,
            status=p.ingestion_status,
            job_type_name=jt_name,
            total_questions=p.total_questions,
            created_at=p.created_at,
        )
        for p, jt_name in recent_rows
    ]

    return AdminDashboardResponse(
        stats=stats,
        timeline=timeline,
        prediction_health=prediction_health,
        recent_activity=recent_activity,
    )
