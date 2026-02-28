"""
Admin Pattern-Analytics Endpoints
==================================
GET /api/v1/admin/pattern-analytics/year-by-year/{job_type_id}
GET /api/v1/admin/pattern-analytics/repeat-questions/{job_type_id}
GET /api/v1/admin/pattern-analytics/compare-job-types
GET /api/v1/admin/pattern-analytics/prediction-accuracy/{prediction_id}
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, and_
from sqlalchemy.orm import selectinload

from app.dependencies import DBSession, require_admin
from app.models.job_type import JobType
from app.models.paper import Paper
from app.models.prediction import Prediction
from app.models.question import Question
from app.models.topic import Topic
from app.models.topic_frequency import TopicFrequencyByJob
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


# ═══════════════════════════════════════════════════════════
# Year-by-Year topic frequency data (for line chart)
# ═══════════════════════════════════════════════════════════

@router.get(
    "/pattern-analytics/year-by-year/{job_type_id}",
    summary="Year-by-year topic frequency breakdown",
)
async def get_year_by_year(
    job_type_id: UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
    top_n: int = Query(8, ge=1, le=20, description="Top N topics to include"),
):
    """Return per-year per-topic frequency data for trend visualisation."""

    # Validate job type
    job_type = await db.get(JobType, job_type_id)
    if not job_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job type not found")

    # Get all frequency rows for this job type, joined with topic names
    q = (
        select(TopicFrequencyByJob, Topic.name, Topic.display_name)
        .join(Topic, TopicFrequencyByJob.topic_id == Topic.id)
        .where(TopicFrequencyByJob.job_type_id == job_type_id)
        .order_by(TopicFrequencyByJob.year.asc())
    )
    rows = (await db.execute(q)).all()

    if not rows:
        return {"job_type_id": str(job_type_id), "job_type_name": job_type.name, "years": [], "topics": [], "series": []}

    # Determine top N topics by total question_count
    topic_totals: dict[str, int] = {}
    for tf, name, display in rows:
        topic_totals[name] = topic_totals.get(name, 0) + tf.question_count

    top_topics = sorted(topic_totals, key=lambda t: topic_totals[t], reverse=True)[:top_n]

    # Build year → topic → percentage map
    years_set: set[int] = set()
    data_map: dict[int, dict[str, float]] = {}
    topic_display_map: dict[str, str] = {}

    for tf, name, display in rows:
        if name not in top_topics:
            continue
        years_set.add(tf.year)
        topic_display_map[name] = display
        data_map.setdefault(tf.year, {})[name] = tf.percentage_of_paper

    years = sorted(years_set)

    # Build series: one entry per year with topic percentages
    series = []
    for yr in years:
        entry: dict = {"year": yr}
        for tn in top_topics:
            entry[tn] = round(data_map.get(yr, {}).get(tn, 0), 2)
        series.append(entry)

    topics = [{"name": tn, "display_name": topic_display_map.get(tn, tn)} for tn in top_topics]

    return {
        "job_type_id": str(job_type_id),
        "job_type_name": job_type.name,
        "years": years,
        "topics": topics,
        "series": series,
    }


# ═══════════════════════════════════════════════════════════
# Repeat Questions (for tracker table)
# ═══════════════════════════════════════════════════════════

@router.get(
    "/pattern-analytics/repeat-questions/{job_type_id}",
    summary="Repeated questions with full details",
)
async def get_repeat_questions(
    job_type_id: UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
):
    """Return repeated questions sorted by repeat_count desc."""

    job_type = await db.get(JobType, job_type_id)
    if not job_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job type not found")

    # Get paper IDs for this job type
    paper_ids_q = select(Paper.id).where(
        Paper.job_type_id == job_type_id,
        Paper.ingestion_status == "completed",
    )
    paper_ids = [r for (r,) in (await db.execute(paper_ids_q)).all()]

    if not paper_ids:
        return {"items": [], "total": 0, "page": page, "per_page": per_page}

    # Count total repeat questions
    count_q = (
        select(func.count(Question.id))
        .where(Question.paper_id.in_(paper_ids), Question.is_repeated.is_(True))
    )
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch paginated repeat questions
    skip = (page - 1) * per_page
    q = (
        select(Question, Topic.name.label("topic_name"), Topic.display_name.label("topic_display"),
               Paper.year.label("paper_year"))
        .outerjoin(Topic, Question.topic_id == Topic.id)
        .join(Paper, Question.paper_id == Paper.id)
        .where(Question.paper_id.in_(paper_ids), Question.is_repeated.is_(True))
        .order_by(Question.repeat_count.desc(), Question.created_at.desc())
        .offset(skip)
        .limit(per_page)
    )
    rows = (await db.execute(q)).all()

    items = []
    for question, topic_name, topic_display, paper_year in rows:
        items.append({
            "id": str(question.id),
            "question_text": question.question_text,
            "topic_name": topic_name or "Uncategorised",
            "topic_display_name": topic_display or topic_name or "Uncategorised",
            "repeat_count": question.repeat_count,
            "similarity_group_id": str(question.similarity_group_id) if question.similarity_group_id else None,
            "year_appeared": question.year_appeared or paper_year,
            "difficulty_score": question.difficulty_score,
            "fact_extracted": question.fact_extracted,
        })

    return {"items": items, "total": total, "page": page, "per_page": per_page}


# ═══════════════════════════════════════════════════════════
# Compare Job Types (radar chart data)
# ═══════════════════════════════════════════════════════════

@router.get(
    "/pattern-analytics/compare-job-types",
    summary="Compare topic ratios across multiple job types",
)
async def compare_job_types(
    db: DBSession,
    admin: User = Depends(require_admin),
    job_type_ids: str = Query(..., description="Comma-separated job type IDs"),
    top_n: int = Query(8, ge=3, le=15, description="Top N topics to compare"),
):
    """Return normalised topic percentages for multiple job types (radar chart)."""

    ids = [UUID(x.strip()) for x in job_type_ids.split(",") if x.strip()]
    if len(ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least 2 job_type_ids",
        )

    # Fetch job type names
    jt_q = select(JobType).where(JobType.id.in_(ids))
    jt_rows = (await db.execute(jt_q)).scalars().all()
    jt_name_map = {str(jt.id): jt.name for jt in jt_rows}

    # For each job type, get the latest year's topic frequencies
    all_data: dict[str, dict[str, float]] = {}  # jt_id → {topic_name: pct}
    global_topic_totals: dict[str, float] = {}

    for jt_id in ids:
        jt_id_str = str(jt_id)
        # Latest year for this job type
        latest_q = select(func.max(TopicFrequencyByJob.year)).where(
            TopicFrequencyByJob.job_type_id == jt_id
        )
        latest_year = (await db.execute(latest_q)).scalar()
        if not latest_year:
            all_data[jt_id_str] = {}
            continue

        freq_q = (
            select(TopicFrequencyByJob, Topic.name, Topic.display_name)
            .join(Topic, TopicFrequencyByJob.topic_id == Topic.id)
            .where(TopicFrequencyByJob.job_type_id == jt_id, TopicFrequencyByJob.year == latest_year)
        )
        rows = (await db.execute(freq_q)).all()

        jt_data: dict[str, float] = {}
        for tf, tname, _ in rows:
            jt_data[tname] = tf.percentage_of_paper
            global_topic_totals[tname] = global_topic_totals.get(tname, 0) + tf.percentage_of_paper
        all_data[jt_id_str] = jt_data

    # Pick top N topics across all job types
    top_topics = sorted(global_topic_totals, key=lambda t: global_topic_totals[t], reverse=True)[:top_n]

    # Get display names
    topic_display_q = select(Topic.name, Topic.display_name).where(Topic.name.in_(top_topics))
    topic_display_rows = (await db.execute(topic_display_q)).all()
    display_map = {name: display for name, display in topic_display_rows}

    # Build radar series: one row per topic, one key per job type
    series = []
    for tn in top_topics:
        row: dict = {"topic": display_map.get(tn, tn)}
        for jt_id_str, jt_data in all_data.items():
            row[jt_name_map.get(jt_id_str, jt_id_str)] = round(jt_data.get(tn, 0), 2)
        series.append(row)

    job_types = [{"id": jt_id_str, "name": jt_name_map.get(jt_id_str, jt_id_str)} for jt_id_str in [str(i) for i in ids]]

    return {"job_types": job_types, "topics": top_topics, "series": series}


# ═══════════════════════════════════════════════════════════
# Prediction Accuracy Retrospective
# ═══════════════════════════════════════════════════════════

@router.get(
    "/pattern-analytics/prediction-accuracy/{prediction_id}",
    summary="Compare prediction against an actual paper",
)
async def prediction_accuracy(
    prediction_id: UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
    actual_paper_id: UUID | None = Query(None, description="Actual paper to compare against"),
):
    """Compare a prediction's topic distribution against the actual paper."""

    pred = await db.get(Prediction, prediction_id)
    if not pred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")

    # Prediction topic distribution
    pred_dist: dict[str, float] = pred.topic_distribution or {}

    # If we have an actual paper, compute its topic distribution
    actual_dist: dict[str, float] = {}
    paper_info = None

    if actual_paper_id:
        paper = await db.get(Paper, actual_paper_id)
        if not paper:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

        paper_info = {
            "id": str(paper.id),
            "year": paper.year,
            "title": paper.title,
        }

        # Count questions per topic for the actual paper
        q = (
            select(Topic.name, func.count(Question.id))
            .join(Topic, Question.topic_id == Topic.id)
            .where(Question.paper_id == actual_paper_id)
            .group_by(Topic.name)
        )
        rows = (await db.execute(q)).all()
        total_q = sum(cnt for _, cnt in rows) if rows else 1

        for tname, cnt in rows:
            actual_dist[tname] = round(cnt / total_q * 100, 2)

    # Merge all topics from both distributions
    all_topics = sorted(set(list(pred_dist.keys()) + list(actual_dist.keys())))

    comparison = []
    total_diff = 0.0
    for tn in all_topics:
        p_val = round(pred_dist.get(tn, 0), 2)
        a_val = round(actual_dist.get(tn, 0), 2)
        diff = round(abs(p_val - a_val), 2)
        total_diff += diff
        comparison.append({
            "topic": tn,
            "predicted_pct": p_val,
            "actual_pct": a_val,
            "difference": diff,
        })

    accuracy_score = round(max(0, 100 - total_diff / 2), 2) if actual_paper_id else None

    return {
        "prediction_id": str(pred.id),
        "prediction_title": pred.title,
        "prediction_date": str(pred.prediction_date),
        "confidence_score": pred.confidence_score,
        "paper_count_basis": pred.paper_count_basis,
        "actual_paper": paper_info,
        "comparison": comparison,
        "accuracy_score": accuracy_score,
        "total_predicted_topics": len(pred_dist),
        "total_actual_topics": len(actual_dist),
    }
