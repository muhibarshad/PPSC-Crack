"""
Stories endpoint — Story Document Generation & Incremental Update API
======================================================================
POST /api/v1/stories/generate/{topic_id}                → enqueue full generation
POST /api/v1/stories/generate-batch                     → enqueue all eligible topics
POST /api/v1/stories/update/{topic_id}/paper/{paper_id} → incremental update from paper
POST /api/v1/stories/update/{topic_id}/facts            → incremental update from fact list
GET  /api/v1/stories/{topic_id}                         → read story document
GET  /api/v1/stories/eligible                           → list topics eligible for generation
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.dependencies import DBSession
from app.models.question import Question
from app.models.topic import Topic
from app.schemas.story import (
    EligibleTopicItem,
    EligibleTopicsResponse,
    IncrementalFactsUpdateRequest,
    IncrementalUpdateResponse,
    StoryBatchTaskResponse,
    StoryDocumentResponse,
    StoryGenerateRequest,
    StoryTaskResponse,
)
from app.services.story_engine import MIN_QUESTIONS_THRESHOLD

logger = logging.getLogger(__name__)

router = APIRouter()


# ─────────────────────────────────────────────────────────────
# POST /generate/{topic_id} — trigger single-topic generation
# ─────────────────────────────────────────────────────────────

@router.post(
    "/generate/{topic_id}",
    response_model=StoryTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue story generation for a topic",
)
async def generate_story(
    topic_id: UUID,
    db: DBSession,
    body: StoryGenerateRequest | None = None,
):
    """Enqueue a Celery task to generate (or regenerate) the story document
    for the given topic.  Returns immediately with the task ID.

    Set ``force=true`` in the body to regenerate even when a story exists
    or the topic has fewer than 10 questions.
    """
    # Verify topic exists
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic {topic_id} not found",
        )

    force = body.force if body else False

    from app.tasks.story_generation import generate_story_document

    task = generate_story_document.apply_async(
        args=[str(topic_id)],
        kwargs={"force": force},
        queue="ai_pipeline",
    )

    return StoryTaskResponse(
        task_id=task.id,
        topic_id=topic_id,
        status="queued",
        message=f"Story generation {'(forced) ' if force else ''}enqueued for '{topic.display_name}'.",
    )


# ─────────────────────────────────────────────────────────────
# POST /generate-batch — trigger batch generation
# ─────────────────────────────────────────────────────────────

@router.post(
    "/generate-batch",
    response_model=StoryBatchTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue batch story generation for all eligible topics",
)
async def generate_stories_batch():
    """Scan all topics with 10+ questions and no existing story, and
    enqueue a single Celery task to generate them all.
    """
    from app.tasks.story_generation import batch_generate_stories

    task = batch_generate_stories.apply_async(queue="ai_pipeline")

    return StoryBatchTaskResponse(
        task_id=task.id,
        status="queued",
        message="Batch story generation task enqueued.",
    )


# ─────────────────────────────────────────────────────────────
# POST /update/{topic_id}/paper/{paper_id} — incremental update from paper
# ─────────────────────────────────────────────────────────────

@router.post(
    "/update/{topic_id}/paper/{paper_id}",
    response_model=IncrementalUpdateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue incremental story update from a paper",
)
async def incremental_update_from_paper(
    topic_id: UUID,
    paper_id: UUID,
    db: DBSession,
):
    """Enqueue a Celery task to incrementally update the story document
    for a topic using new facts extracted from a specific paper.

    This **never regenerates the full document** — it embeds the new facts,
    matches them to existing sections via cosine similarity, and surgically
    updates only the affected sections with GPT-4o.

    If the topic has no story document yet, the task will return a
    ``no_story`` status.
    """
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic {topic_id} not found",
        )

    from app.tasks.story_generation import incremental_story_update

    task = incremental_story_update.apply_async(
        args=[str(topic_id), str(paper_id)],
        queue="ai_pipeline",
    )

    return IncrementalUpdateResponse(
        task_id=task.id,
        topic_id=topic_id,
        paper_id=paper_id,
        status="queued",
        message=(
            f"Incremental story update enqueued for topic '{topic.display_name}' "
            f"with paper {paper_id}."
        ),
    )


# ─────────────────────────────────────────────────────────────
# POST /update/{topic_id}/facts — incremental update from fact list
# ─────────────────────────────────────────────────────────────

@router.post(
    "/update/{topic_id}/facts",
    response_model=IncrementalUpdateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue incremental story update from explicit facts",
)
async def incremental_update_from_facts(
    topic_id: UUID,
    body: IncrementalFactsUpdateRequest,
    db: DBSession,
):
    """Enqueue a Celery task to incrementally update the story document
    for a topic using an explicit list of facts provided in the request body.

    Useful for admin-driven updates or reprocessing without a specific paper.
    """
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic {topic_id} not found",
        )

    if not body.facts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one fact must be provided.",
        )

    from app.tasks.story_generation import incremental_facts_update

    task = incremental_facts_update.apply_async(
        args=[str(topic_id)],
        kwargs={"fact_texts": body.facts},
        queue="ai_pipeline",
    )

    return IncrementalUpdateResponse(
        task_id=task.id,
        topic_id=topic_id,
        status="queued",
        message=(
            f"Incremental story update enqueued for topic '{topic.display_name}' "
            f"with {len(body.facts)} facts."
        ),
    )


# ─────────────────────────────────────────────────────────────
# GET /{topic_id} — read story document
# ─────────────────────────────────────────────────────────────

@router.get(
    "/{topic_id}",
    response_model=StoryDocumentResponse,
    summary="Get the story document for a topic",
)
async def get_story(topic_id: UUID, db: DBSession):
    """Return the stored story document for a topic.  Returns ``null``
    for ``story_document`` if one hasn't been generated yet.
    """
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic {topic_id} not found",
        )

    return StoryDocumentResponse(
        topic_id=topic.id,
        topic_name=topic.name,
        display_name=topic.display_name,
        story_document=topic.story_document,
        story_word_count=topic.story_word_count,
        story_last_updated=topic.story_last_updated,
        total_questions=topic.total_questions,
    )


# ─────────────────────────────────────────────────────────────
# GET /eligible — list topics eligible for story generation
# ─────────────────────────────────────────────────────────────

@router.get(
    "/eligible",
    response_model=EligibleTopicsResponse,
    summary="List topics eligible for story generation",
)
async def list_eligible_topics(db: DBSession):
    """Return all topics with their question counts and whether they
    already have a story document.  Only includes topics with at least
    one question.
    """
    result = await db.execute(
        select(
            Topic.id,
            Topic.display_name,
            func.count(Question.id).label("q_count"),
            Topic.story_document,
        )
        .outerjoin(Question, Question.topic_id == Topic.id)
        .group_by(Topic.id, Topic.display_name, Topic.story_document)
        .having(func.count(Question.id) >= MIN_QUESTIONS_THRESHOLD)
        .order_by(func.count(Question.id).desc())
    )

    items = [
        EligibleTopicItem(
            topic_id=row.id,
            display_name=row.display_name,
            question_count=row.q_count,
            has_story=row.story_document is not None,
        )
        for row in result.all()
    ]

    return EligibleTopicsResponse(topics=items, total=len(items))
