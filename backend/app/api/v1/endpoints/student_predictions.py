"""
Student Predictions endpoint — GET /api/v1/student/predictions/latest
=====================================================================
Returns the latest published prediction for authenticated premium students.
Enriches each question with topic-frequency probability for the UI badge.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func

from app.dependencies import DBSession, get_current_user, require_premium
from app.crud.crud_prediction import crud_prediction
from app.models.prediction import Prediction
from app.models.topic_frequency import TopicFrequencyByJob
from app.models.topic import Topic
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/predictions/latest",
    summary="Get the latest published predicted paper (premium)",
)
async def get_latest_prediction(
    db: DBSession,
    current_user: User = Depends(get_current_user),
    job_type_id: UUID | None = Query(
        None,
        description="Filter by job type. If omitted, uses student's first selected job type.",
    ),
):
    """Return the latest published prediction in exam-ready format.

    • Free users receive a 403 with an ``upgrade_required`` flag so the
      frontend can render the upgrade prompt instead of a generic error.
    • Questions are annotated with ``probability`` derived from topic
      frequency data for the given job type.
    """

    # ── Premium gate ─────────────────────────────────────────
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Premium subscription required to access predicted papers",
                "upgrade_required": True,
                "subscription_tier": current_user.subscription_tier,
            },
        )

    # ── Resolve job type ─────────────────────────────────────
    effective_job_type_id = job_type_id
    if not effective_job_type_id and current_user.selected_job_types:
        effective_job_type_id = current_user.selected_job_types[0]

    # ── Fetch latest published prediction ────────────────────
    pred = await crud_prediction.get_latest_published(
        db, job_type_id=effective_job_type_id
    )

    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published prediction found",
        )

    # ── Build topic → probability map from frequency data ────
    topic_probability: dict[str, float] = {}
    if pred.job_type_id:
        # Get the latest year's frequency data
        latest_year_q = (
            select(func.max(TopicFrequencyByJob.year))
            .where(TopicFrequencyByJob.job_type_id == pred.job_type_id)
        )
        latest_year = (await db.execute(latest_year_q)).scalar()

        if latest_year:
            freq_q = (
                select(TopicFrequencyByJob, Topic)
                .join(Topic, TopicFrequencyByJob.topic_id == Topic.id)
                .where(
                    TopicFrequencyByJob.job_type_id == pred.job_type_id,
                    TopicFrequencyByJob.year == latest_year,
                )
            )
            freq_rows = (await db.execute(freq_q)).all()
            for row in freq_rows:
                tf = row[0]
                topic = row[1]
                topic_probability[topic.name.lower()] = round(
                    tf.percentage_of_paper, 1
                )

    # ── Enrich questions with probability ────────────────────
    questions_raw = []
    if pred.questions_json and isinstance(pred.questions_json, dict):
        questions_raw = pred.questions_json.get("questions", [])

    ca_raw = []
    if pred.current_affairs_json and isinstance(pred.current_affairs_json, dict):
        ca_raw = pred.current_affairs_json.get("questions", [])

    all_questions = []
    for i, q in enumerate(questions_raw + ca_raw, start=1):
        topic_name = q.get("topic_name", "")
        prob = topic_probability.get(topic_name.lower(), 0.0)
        all_questions.append({
            "question_number": i,
            "question_text": q.get("question_text", ""),
            "option_a": q.get("option_a", ""),
            "option_b": q.get("option_b", ""),
            "option_c": q.get("option_c", ""),
            "option_d": q.get("option_d", ""),
            "correct_answer": q.get("correct_answer", ""),
            "topic_name": topic_name,
            "subtopic": q.get("subtopic"),
            "difficulty_score": q.get("difficulty_score", 0.5),
            "confidence": q.get("confidence", 0.0),
            "is_current_affairs": q.get("is_current_affairs", False),
            "probability": prob,
        })

    # ── Topic distribution summary for results screen ────────
    topic_summary: dict[str, dict] = {}
    for q in all_questions:
        tn = q["topic_name"] or "Uncategorized"
        if tn not in topic_summary:
            topic_summary[tn] = {
                "topic_name": tn,
                "question_count": 0,
                "probability": q["probability"],
            }
        topic_summary[tn]["question_count"] += 1

    jt = pred.job_type_rel

    return {
        "id": str(pred.id),
        "title": pred.title,
        "job_type_id": str(pred.job_type_id),
        "job_type_name": jt.name if jt else None,
        "prediction_date": pred.prediction_date.isoformat(),
        "total_questions": len(all_questions),
        "confidence_score": pred.confidence_score,
        "paper_count_basis": pred.paper_count_basis,
        "pattern_consistency": pred.pattern_consistency,
        "published_at": pred.published_at.isoformat() if pred.published_at else None,
        "questions": all_questions,
        "topic_distribution": list(topic_summary.values()),
        "time_limit_minutes": max(len(all_questions), 60),
    }
