"""
Pattern Update Service
=======================
Updates ``topic_frequency_by_job`` table after paper ingestion.
Also refreshes topic-level aggregate stats.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import date
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic import Topic
from app.models.topic_frequency import TopicFrequencyByJob
from app.models.question import Question
from app.schemas.topic_frequency import TopicFrequencyCreate
from app.crud.crud_topic_frequency import crud_topic_frequency

logger = logging.getLogger(__name__)


async def update_topic_frequencies(
    db: AsyncSession,
    *,
    paper_id: UUID,
    job_type_id: UUID,
    paper_year: int,
    total_questions: int,
) -> dict:
    """Recompute topic frequencies for this paper's job type + year.

    Steps:
    1. Count questions per topic for the given paper.
    2. Upsert into ``topic_frequency_by_job``.
    3. Update aggregate stats on each ``Topic`` row.

    Returns
    -------
    dict
        Summary of updates.
    """
    # ── 1. Count questions by topic for this paper ───────────
    stmt = (
        select(Question.topic_id, func.count().label("cnt"))
        .where(Question.paper_id == paper_id)
        .where(Question.topic_id.isnot(None))
        .group_by(Question.topic_id)
    )
    result = await db.execute(stmt)
    topic_counts: dict[UUID, int] = {row.topic_id: row.cnt for row in result.all()}

    if not topic_counts:
        logger.warning("No classified questions found for paper %s", paper_id)
        return {"topics_updated": 0}

    # ── 2. Upsert frequency rows ────────────────────────────
    for topic_id, count in topic_counts.items():
        pct = round((count / total_questions) * 100, 2) if total_questions > 0 else 0.0
        await crud_topic_frequency.upsert(
            db,
            obj_in=TopicFrequencyCreate(
                topic_id=topic_id,
                job_type_id=job_type_id,
                year=paper_year,
                question_count=count,
                percentage_of_paper=pct,
            ),
        )

    # ── 3. Update topic aggregate stats ──────────────────────
    paper_date = date(paper_year, 1, 1)

    for topic_id in topic_counts:
        topic = await db.get(Topic, topic_id)
        if not topic:
            continue

        # Total questions across all papers
        total_q_result = await db.execute(
            select(func.count())
            .select_from(Question)
            .where(Question.topic_id == topic_id)
        )
        topic.total_questions = total_q_result.scalar() or 0

        # Update first/last appeared
        if topic.first_appeared_date is None or paper_date < topic.first_appeared_date:
            topic.first_appeared_date = paper_date
        if topic.last_appeared_date is None or paper_date > topic.last_appeared_date:
            topic.last_appeared_date = paper_date

        # Frequency score = total questions / total papers with this topic
        freq_rows_result = await db.execute(
            select(func.count())
            .select_from(TopicFrequencyByJob)
            .where(TopicFrequencyByJob.topic_id == topic_id)
        )
        freq_row_count = freq_rows_result.scalar() or 1
        topic.frequency_score = round(topic.total_questions / freq_row_count, 2)

        db.add(topic)

    await db.flush()

    logger.info(
        "Updated frequencies for %d topics (paper=%s, job=%s, year=%d)",
        len(topic_counts), paper_id, job_type_id, paper_year,
    )

    return {
        "topics_updated": len(topic_counts),
        "topic_breakdown": {str(k): v for k, v in topic_counts.items()},
    }
