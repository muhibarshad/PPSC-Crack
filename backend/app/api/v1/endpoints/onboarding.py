"""
Onboarding API — Student first-login onboarding flow
======================================================
POST /api/v1/onboarding/analyze   — Get AI analysis for selected job types
POST /api/v1/onboarding/complete  — Save selections + return learning path
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select

from app.crud.crud_job_type import crud_job_type
from app.crud.crud_user import crud_user
from app.dependencies import DBSession, get_current_user
from app.models.job_type import JobType
from app.models.pattern_snapshot import PatternSnapshot
from app.models.topic import Topic
from app.models.topic_frequency import TopicFrequencyByJob
from app.models.user import User
from app.schemas.onboarding import (
    JobAnalysis,
    LearningPathPreview,
    LearningPathTopic,
    OnboardingAnalysisResponse,
    OnboardingCompleteRequest,
    OnboardingCompleteResponse,
    TopicRatioEntry,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Average reading speed: ~200 words per minute → story docs
WORDS_PER_MINUTE = 200


async def _build_analysis(db: DBSession, job_type_ids: list[UUID]) -> list[JobAnalysis]:
    """Build AI analysis for each job type."""
    analyses: list[JobAnalysis] = []

    for jt_id in job_type_ids:
        job_type = await db.get(JobType, jt_id)
        if not job_type:
            continue

        # ── Get latest snapshot confidence
        snap_q = (
            select(PatternSnapshot)
            .where(PatternSnapshot.job_type_id == jt_id)
            .order_by(PatternSnapshot.created_at.desc())
            .limit(1)
        )
        snapshot = (await db.execute(snap_q)).scalar_one_or_none()
        confidence = snapshot.confidence_score if snapshot else 0.0

        # ── Get topic frequencies for latest year
        latest_year_q = (
            select(func.max(TopicFrequencyByJob.year))
            .where(TopicFrequencyByJob.job_type_id == jt_id)
        )
        latest_year = (await db.execute(latest_year_q)).scalar()

        topic_ratios: list[TopicRatioEntry] = []
        total_topics = 0
        total_story_words = 0

        if latest_year:
            freq_q = (
                select(TopicFrequencyByJob, Topic)
                .join(Topic, TopicFrequencyByJob.topic_id == Topic.id)
                .where(
                    TopicFrequencyByJob.job_type_id == jt_id,
                    TopicFrequencyByJob.year == latest_year,
                )
                .order_by(TopicFrequencyByJob.percentage_of_paper.desc())
            )
            freq_rows = (await db.execute(freq_q)).all()

            for row in freq_rows:
                tf = row[0]
                topic = row[1]
                topic_ratios.append(TopicRatioEntry(
                    topic_name=topic.name,
                    display_name=topic.display_name,
                    percentage=tf.percentage_of_paper,
                    question_count=tf.question_count,
                ))
                total_topics += 1
                total_story_words += topic.story_word_count or 0
        elif job_type.topic_ratios:
            # Fallback: use the stored topic_ratios JSON on the job type
            for name, pct in job_type.topic_ratios.items():
                topic_ratios.append(TopicRatioEntry(
                    topic_name=name,
                    display_name=name.replace("_", " ").title(),
                    percentage=float(pct) if isinstance(pct, (int, float)) else 0.0,
                    question_count=0,
                ))
                total_topics += 1

        # Estimated prep time: topic count × 2 hrs base + story reading time
        reading_hours = total_story_words / WORDS_PER_MINUTE / 60 if total_story_words else 0
        estimated_hours = round(total_topics * 2.0 + reading_hours, 1)

        analyses.append(JobAnalysis(
            job_type_id=jt_id,
            job_type_name=job_type.name,
            topic_ratios=topic_ratios,
            estimated_prep_hours=estimated_hours,
            confidence_score=confidence,
            total_papers_analyzed=job_type.total_papers,
            total_topics=total_topics,
        ))

    return analyses


async def _build_learning_path(
    db: DBSession, job_type_ids: list[UUID],
) -> LearningPathPreview:
    """Build a priority-ordered learning path across all selected job types."""

    # Gather unique topic IDs across all selected jobs, weighted by frequency
    topic_scores: dict[UUID, dict] = {}

    for jt_id in job_type_ids:
        latest_year_q = (
            select(func.max(TopicFrequencyByJob.year))
            .where(TopicFrequencyByJob.job_type_id == jt_id)
        )
        latest_year = (await db.execute(latest_year_q)).scalar()
        if not latest_year:
            continue

        freq_q = (
            select(TopicFrequencyByJob, Topic)
            .join(Topic, TopicFrequencyByJob.topic_id == Topic.id)
            .where(
                TopicFrequencyByJob.job_type_id == jt_id,
                TopicFrequencyByJob.year == latest_year,
            )
        )
        rows = (await db.execute(freq_q)).all()

        for row in rows:
            tf = row[0]
            topic = row[1]
            if topic.id not in topic_scores:
                topic_scores[topic.id] = {
                    "topic": topic,
                    "score": 0.0,
                    "question_count": 0,
                }
            # Accumulate score across job types
            topic_scores[topic.id]["score"] += tf.percentage_of_paper
            topic_scores[topic.id]["question_count"] += tf.question_count

    # Sort by accumulated score descending
    sorted_topics = sorted(
        topic_scores.values(), key=lambda x: x["score"], reverse=True,
    )

    # Take top 5
    learning_topics: list[LearningPathTopic] = []
    for i, entry in enumerate(sorted_topics[:5], start=1):
        t: Topic = entry["topic"]
        word_count = t.story_word_count or 0
        read_minutes = max(1, round(word_count / WORDS_PER_MINUTE)) if word_count else 0
        learning_topics.append(LearningPathTopic(
            rank=i,
            topic_id=t.id,
            topic_name=t.name,
            display_name=t.display_name,
            frequency_score=round(entry["score"], 2),
            trend_direction=t.trend_direction,
            story_available=bool(t.story_document),
            estimated_read_minutes=read_minutes,
        ))

    return LearningPathPreview(
        topics=learning_topics,
        total_topics_in_path=len(sorted_topics),
    )


# ═══════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════


@router.post(
    "/analyze",
    response_model=OnboardingAnalysisResponse,
    summary="Get AI analysis for selected job types",
)
async def analyze_job_types(
    body: OnboardingCompleteRequest,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Return topic-ratio breakdowns, confidence scores, and prep time estimates
    for the given job types. Called during step 2 of onboarding."""

    # Validate all job type IDs exist
    for jt_id in body.selected_job_type_ids:
        jt = await db.get(JobType, jt_id)
        if not jt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job type {jt_id} not found",
            )

    analyses = await _build_analysis(db, body.selected_job_type_ids)
    return OnboardingAnalysisResponse(analyses=analyses)


@router.post(
    "/complete",
    response_model=OnboardingCompleteResponse,
    summary="Complete onboarding — save job selections",
)
async def complete_onboarding(
    body: OnboardingCompleteRequest,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Save the student's selected job types and return their personalized
    learning path preview. Final step of onboarding."""

    # Validate all job type IDs exist
    for jt_id in body.selected_job_type_ids:
        jt = await db.get(JobType, jt_id)
        if not jt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job type {jt_id} not found",
            )

    # Save to user profile
    await crud_user.set_selected_job_types(
        db, id=current_user.id, job_type_ids=body.selected_job_type_ids,
    )
    await db.commit()

    # Build analysis + learning path
    analyses = await _build_analysis(db, body.selected_job_type_ids)
    learning_path = await _build_learning_path(db, body.selected_job_type_ids)

    logger.info(
        "Onboarding complete for user %s — selected %d job types",
        current_user.id,
        len(body.selected_job_type_ids),
    )

    return OnboardingCompleteResponse(
        message="Onboarding complete! Your personalized learning path is ready.",
        selected_job_type_ids=body.selected_job_type_ids,
        analyses=analyses,
        learning_path=learning_path,
    )
