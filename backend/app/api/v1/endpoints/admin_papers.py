"""
Admin Papers Library Endpoints
================================
GET    /api/v1/admin/papers                   — list all papers with filters & sort
GET    /api/v1/admin/papers/:id               — paper detail with questions
PUT    /api/v1/admin/papers/:id               — update paper metadata
DELETE /api/v1/admin/papers/:id               — delete a paper
POST   /api/v1/admin/papers/:id/reprocess     — re-trigger AI pipeline
PUT    /api/v1/admin/papers/:id/questions/:qid — update a single question inline
POST   /api/v1/admin/papers                   — ingest a new paper (text-paste mode)
GET    /api/v1/admin/papers/:id/status         — poll ingestion progress
GET    /api/v1/admin/papers/:id/status/:task_id — poll with task ID
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.orm import selectinload

from app.dependencies import DBSession, require_admin
from app.models.job_type import JobType
from app.models.paper import Paper
from app.models.question import Question
from app.models.topic import Topic
from app.models.user import User
from app.schemas.admin_papers import (
    AdminPaperCard,
    AdminPaperDetail,
    AdminPaperUpdate,
    AdminPapersListResponse,
    AdminQuestionUpdate,
    QuestionInPaper,
    ReprocessResponse,
    TopicPill,
)
from app.schemas.paper_ingestion import (
    PaperIngestRequest,
    PaperIngestResponse,
    ParseSummary,
    IngestionStatusResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ═══════════════════════════════════════════════════════════
# GET /papers — List all papers with filters, search, sort
# ═══════════════════════════════════════════════════════════

@router.get(
    "/papers",
    response_model=AdminPapersListResponse,
    summary="List all papers with filters & sorting",
)
async def list_papers(
    db: DBSession,
    admin: User = Depends(require_admin),
    # Pagination
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    # Search
    search: str | None = Query(None, description="Search in paper title"),
    # Filters
    job_type_ids: str | None = Query(None, description="Comma-separated job type UUIDs"),
    status_filter: str | None = Query(None, alias="status", description="pending,processing,completed,failed"),
    year_min: int | None = Query(None, description="Min paper year"),
    year_max: int | None = Query(None, description="Max paper year"),
    topic_id: str | None = Query(None, description="Filter by topic UUID"),
    # Sort
    sort: str = Query("newest", description="newest|oldest|job_type|questions"),
):
    """Return a paginated list of papers with job type, topics, and repeat counts."""

    query = select(Paper).join(JobType, Paper.job_type_id == JobType.id)
    count_query = select(func.count(Paper.id)).join(JobType, Paper.job_type_id == JobType.id)

    # ── Search ───────────────────────────────────────────
    if search:
        search_term = f"%{search.strip()}%"
        query = query.where(Paper.title.ilike(search_term))
        count_query = count_query.where(Paper.title.ilike(search_term))

    # ── Job type filter ──────────────────────────────────
    if job_type_ids:
        try:
            jt_uuids = [uuid.UUID(x.strip()) for x in job_type_ids.split(",") if x.strip()]
            if jt_uuids:
                query = query.where(Paper.job_type_id.in_(jt_uuids))
                count_query = count_query.where(Paper.job_type_id.in_(jt_uuids))
        except ValueError:
            pass

    # ── Status filter ────────────────────────────────────
    if status_filter:
        statuses = [s.strip() for s in status_filter.split(",") if s.strip()]
        if statuses:
            query = query.where(Paper.ingestion_status.in_(statuses))
            count_query = count_query.where(Paper.ingestion_status.in_(statuses))

    # ── Year range ───────────────────────────────────────
    if year_min:
        query = query.where(Paper.paper_year >= year_min)
        count_query = count_query.where(Paper.paper_year >= year_min)
    if year_max:
        query = query.where(Paper.paper_year <= year_max)
        count_query = count_query.where(Paper.paper_year <= year_max)

    # ── Topic filter ─────────────────────────────────────
    if topic_id:
        try:
            tid = uuid.UUID(topic_id.strip())
            paper_ids_with_topic = (
                select(Question.paper_id)
                .where(Question.topic_id == tid)
                .distinct()
                .subquery()
            )
            query = query.where(Paper.id.in_(select(paper_ids_with_topic.c.paper_id)))
            count_query = count_query.where(
                Paper.id.in_(select(paper_ids_with_topic.c.paper_id))
            )
        except ValueError:
            pass

    # ── Sort ─────────────────────────────────────────────
    if sort == "oldest":
        query = query.order_by(Paper.paper_year.asc(), Paper.paper_month.asc().nullslast())
    elif sort == "job_type":
        query = query.order_by(JobType.name.asc(), Paper.paper_year.desc())
    elif sort == "questions":
        query = query.order_by(Paper.total_questions.desc())
    else:
        query = query.order_by(Paper.paper_year.desc(), Paper.paper_month.desc().nullslast(), Paper.created_at.desc())

    # ── Count ────────────────────────────────────────────
    total = (await db.execute(count_query)).scalar() or 0

    # ── Paginate ─────────────────────────────────────────
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    rows = (await db.execute(query)).scalars().all()

    # ── Build response cards ─────────────────────────────
    cards: list[AdminPaperCard] = []
    for paper in rows:
        jt = await db.get(JobType, paper.job_type_id)

        topic_q = (
            select(Topic.id, Topic.name, Topic.display_name, Topic.color_hex)
            .join(Question, Question.topic_id == Topic.id)
            .where(Question.paper_id == paper.id)
            .distinct()
        )
        topic_rows = (await db.execute(topic_q)).all()
        topics_total = len(topic_rows)
        topics = [
            TopicPill(id=r[0], name=r[1], display_name=r[2], color_hex=r[3])
            for r in topic_rows[:5]
        ]

        repeat_count_q = (
            select(func.count(Question.id))
            .where(Question.paper_id == paper.id, Question.is_repeated.is_(True))
        )
        repeat_count = (await db.execute(repeat_count_q)).scalar() or 0

        cards.append(
            AdminPaperCard(
                id=paper.id,
                title=paper.title,
                paper_year=paper.paper_year,
                paper_month=paper.paper_month,
                paper_date=paper.paper_date,
                total_questions=paper.total_questions,
                ingestion_status=paper.ingestion_status,
                repeat_questions_count=repeat_count,
                job_type_id=paper.job_type_id,
                job_type_name=jt.name if jt else "Unknown",
                job_type_slug=jt.slug if jt else "unknown",
                topics=topics,
                topics_total=topics_total,
                source=paper.source,
                created_at=paper.created_at,
                updated_at=paper.updated_at,
            )
        )

    return AdminPapersListResponse(
        papers=cards,
        total=total,
        page=page,
        per_page=per_page,
    )


# ═══════════════════════════════════════════════════════════
# GET /papers/:id — Paper detail with questions
# ═══════════════════════════════════════════════════════════

@router.get(
    "/papers/{paper_id}",
    response_model=AdminPaperDetail,
    summary="Get paper detail with paginated questions",
)
async def get_paper_detail(
    paper_id: uuid.UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
    q_page: int = Query(1, ge=1, alias="questions_page"),
    q_per_page: int = Query(20, ge=1, le=100, alias="questions_per_page"),
):
    """Get full paper details including questions."""
    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    jt = await db.get(JobType, paper.job_type_id)

    topic_q = (
        select(Topic.id, Topic.name, Topic.display_name, Topic.color_hex)
        .join(Question, Question.topic_id == Topic.id)
        .where(Question.paper_id == paper.id)
        .distinct()
    )
    topic_rows = (await db.execute(topic_q)).all()
    topics = [
        TopicPill(id=r[0], name=r[1], display_name=r[2], color_hex=r[3])
        for r in topic_rows
    ]

    q_count = select(func.count(Question.id)).where(Question.paper_id == paper.id)
    questions_total = (await db.execute(q_count)).scalar() or 0

    q_offset = (q_page - 1) * q_per_page
    q_query = (
        select(Question)
        .where(Question.paper_id == paper.id)
        .order_by(Question.question_number.asc())
        .offset(q_offset)
        .limit(q_per_page)
    )
    question_rows = (await db.execute(q_query)).scalars().all()

    questions: list[QuestionInPaper] = []
    for q in question_rows:
        topic_name = None
        if q.topic_id:
            t = await db.get(Topic, q.topic_id)
            topic_name = t.display_name if t else None
        questions.append(
            QuestionInPaper(
                id=q.id,
                question_number=q.question_number,
                question_text=q.question_text,
                option_a=q.option_a,
                option_b=q.option_b,
                option_c=q.option_c,
                option_d=q.option_d,
                correct_answer=q.correct_answer,
                topic_id=q.topic_id,
                topic_name=topic_name,
                subtopic=q.subtopic,
                difficulty_score=q.difficulty_score,
                fact_extracted=q.fact_extracted,
                is_repeated=q.is_repeated,
                repeat_count=q.repeat_count,
                needs_review=q.needs_review,
                admin_notes=q.admin_notes,
                created_at=q.created_at,
            )
        )

    repeat_count_q = (
        select(func.count(Question.id))
        .where(Question.paper_id == paper.id, Question.is_repeated.is_(True))
    )
    repeat_count = (await db.execute(repeat_count_q)).scalar() or 0

    return AdminPaperDetail(
        id=paper.id,
        title=paper.title,
        paper_year=paper.paper_year,
        paper_month=paper.paper_month,
        paper_date=paper.paper_date,
        total_questions=paper.total_questions,
        ingestion_status=paper.ingestion_status,
        source=paper.source,
        raw_scan_data=paper.raw_scan_data,
        job_type_id=paper.job_type_id,
        job_type_name=jt.name if jt else "Unknown",
        job_type_slug=jt.slug if jt else "unknown",
        topics=topics,
        questions=questions,
        questions_total=questions_total,
        questions_page=q_page,
        questions_per_page=q_per_page,
        repeat_questions_count=repeat_count,
        created_at=paper.created_at,
        updated_at=paper.updated_at,
    )


# ═══════════════════════════════════════════════════════════
# PUT /papers/:id — Update paper metadata
# ═══════════════════════════════════════════════════════════

@router.put(
    "/papers/{paper_id}",
    response_model=AdminPaperCard,
    summary="Update paper metadata",
)
async def update_paper(
    paper_id: uuid.UUID,
    body: AdminPaperUpdate,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Update paper metadata."""
    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(paper, field):
            setattr(paper, field, value)

    await db.flush()
    await db.refresh(paper)

    jt = await db.get(JobType, paper.job_type_id)

    topic_q = (
        select(Topic.id, Topic.name, Topic.display_name, Topic.color_hex)
        .join(Question, Question.topic_id == Topic.id)
        .where(Question.paper_id == paper.id)
        .distinct()
    )
    topic_rows = (await db.execute(topic_q)).all()
    topics_total = len(topic_rows)
    topics = [
        TopicPill(id=r[0], name=r[1], display_name=r[2], color_hex=r[3])
        for r in topic_rows[:5]
    ]

    repeat_count_q = (
        select(func.count(Question.id))
        .where(Question.paper_id == paper.id, Question.is_repeated.is_(True))
    )
    repeat_count = (await db.execute(repeat_count_q)).scalar() or 0

    return AdminPaperCard(
        id=paper.id,
        title=paper.title,
        paper_year=paper.paper_year,
        paper_month=paper.paper_month,
        paper_date=paper.paper_date,
        total_questions=paper.total_questions,
        ingestion_status=paper.ingestion_status,
        repeat_questions_count=repeat_count,
        job_type_id=paper.job_type_id,
        job_type_name=jt.name if jt else "Unknown",
        job_type_slug=jt.slug if jt else "unknown",
        topics=topics,
        topics_total=topics_total,
        source=paper.source,
        created_at=paper.created_at,
        updated_at=paper.updated_at,
    )


# ═══════════════════════════════════════════════════════════
# DELETE /papers/:id
# ═══════════════════════════════════════════════════════════

@router.delete(
    "/papers/{paper_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a paper and all its questions",
)
async def delete_paper(
    paper_id: uuid.UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Delete a paper. Cascades to delete all associated questions."""
    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    await db.delete(paper)
    await db.flush()
    logger.info("Paper %s deleted by admin=%s", paper_id, admin.id)


# ═══════════════════════════════════════════════════════════
# POST /papers/:id/reprocess
# ═══════════════════════════════════════════════════════════

@router.post(
    "/papers/{paper_id}/reprocess",
    response_model=ReprocessResponse,
    summary="Re-trigger AI processing for a paper",
)
async def reprocess_paper(
    paper_id: uuid.UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Re-trigger the AI pipeline."""
    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    paper.ingestion_status = "processing"
    await db.flush()

    task_id = None
    try:
        from app.tasks.paper_ingestion import run_ai_pipeline
        task = run_ai_pipeline.delay(
            paper_id=str(paper_id),
            job_type_id=str(paper.job_type_id),
            paper_year=paper.paper_year,
        )
        task_id = task.id
    except Exception as exc:
        logger.warning("Could not dispatch Celery task for reprocess: %s", exc)

    logger.info("Paper %s reprocess triggered by admin=%s", paper_id, admin.id)

    return ReprocessResponse(
        paper_id=paper_id,
        status="processing",
        message="AI pipeline re-triggered successfully",
        task_id=task_id,
    )


# ═══════════════════════════════════════════════════════════
# PUT /papers/:id/questions/:qid — Inline-edit a question
# ═══════════════════════════════════════════════════════════

@router.put(
    "/papers/{paper_id}/questions/{question_id}",
    response_model=QuestionInPaper,
    summary="Update a question inline",
)
async def update_question_inline(
    paper_id: uuid.UUID,
    question_id: uuid.UUID,
    body: AdminQuestionUpdate,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Update a single question within a paper."""
    question = await db.get(Question, question_id)
    if not question or question.paper_id != paper_id:
        raise HTTPException(status_code=404, detail="Question not found in this paper")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(question, field):
            setattr(question, field, value)

    await db.flush()
    await db.refresh(question)

    topic_name = None
    if question.topic_id:
        t = await db.get(Topic, question.topic_id)
        topic_name = t.display_name if t else None

    return QuestionInPaper(
        id=question.id,
        question_number=question.question_number,
        question_text=question.question_text,
        option_a=question.option_a,
        option_b=question.option_b,
        option_c=question.option_c,
        option_d=question.option_d,
        correct_answer=question.correct_answer,
        topic_id=question.topic_id,
        topic_name=topic_name,
        subtopic=question.subtopic,
        difficulty_score=question.difficulty_score,
        fact_extracted=question.fact_extracted,
        is_repeated=question.is_repeated,
        repeat_count=question.repeat_count,
        needs_review=question.needs_review,
        admin_notes=question.admin_notes,
        created_at=question.created_at,
    )


# ═══════════════════════════════════════════════════════════
# POST /papers — Ingest a new paper (text-paste mode)
# ═══════════════════════════════════════════════════════════

@router.post(
    "/papers",
    response_model=PaperIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a new paper (text-paste mode)",
)
async def ingest_paper(
    body: PaperIngestRequest,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Ingest a past paper from pasted text."""
    from app.services.paper_ingestion.pipeline import run_sync_steps
    from app.tasks.paper_ingestion import run_ai_pipeline

    paper_id = uuid.uuid4()

    try:
        sync_summary = await run_sync_steps(
            db,
            paper_id=paper_id,
            job_type_id=body.job_type_id,
            paper_year=body.paper_year,
            paper_month=body.paper_month,
            title=body.title,
            questions_text=body.questions_text,
            answer_key_text=body.answer_key_text,
        )
    except Exception as exc:
        logger.exception("Sync ingestion failed for paper %s: %s", paper_id, exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse paper: {exc}",
        )

    task = run_ai_pipeline.delay(
        paper_id=str(paper_id),
        job_type_id=str(body.job_type_id),
        paper_year=body.paper_year,
    )

    logger.info("Paper %s ingestion started by admin=%s. Task=%s", paper_id, admin.id, task.id)

    return PaperIngestResponse(
        paper_id=paper_id,
        ingestion_status="processing",
        task_id=task.id,
        parse_summary=ParseSummary(
            total_parsed=sync_summary["total_parsed"],
            total_mapped=sync_summary["total_mapped"],
            unmapped_questions=sync_summary["unmapped_questions"],
            unmapped_answers=sync_summary["unmapped_answers"],
            warnings=sync_summary["warnings"],
        ),
        sync_processing_time_ms=sync_summary["sync_processing_time_ms"],
    )


# ═══════════════════════════════════════════════════════════
# GET /papers/:id/status — Poll ingestion status
# ═══════════════════════════════════════════════════════════

@router.get(
    "/papers/{paper_id}/status",
    response_model=IngestionStatusResponse,
    summary="Poll paper ingestion status",
)
async def get_ingestion_status(
    paper_id: uuid.UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
    return IngestionStatusResponse(paper_id=paper_id, ingestion_status=paper.ingestion_status)


@router.get(
    "/papers/{paper_id}/status/{task_id}",
    response_model=IngestionStatusResponse,
    summary="Poll paper ingestion status with task ID",
)
async def get_ingestion_status_with_task(
    paper_id: uuid.UUID,
    task_id: str,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")

    from app.worker import celery_app
    result = celery_app.AsyncResult(task_id)

    response = IngestionStatusResponse(
        paper_id=paper_id,
        ingestion_status=paper.ingestion_status,
        task_id=task_id,
        task_state=result.state,
    )

    if result.ready():
        try:
            response.ai_summary = result.result
        except Exception:
            response.ai_summary = {"error": "Failed to retrieve task result"}

    return response
