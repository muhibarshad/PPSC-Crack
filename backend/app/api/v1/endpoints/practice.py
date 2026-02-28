"""
Student Practice Test API
===========================
GET  /api/v1/student/practice/generate  → generate a fresh set of MCQs
POST /api/v1/student/practice/submit    → score answers, return breakdown, update learning_progress
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4, UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func as sqlfunc

from app.dependencies import DBSession, get_current_user
from app.models.question import Question
from app.models.topic import Topic
from app.models.user import User
from app.schemas.practice import (
    PracticeGenerateParams,
    PracticeGenerateResponse,
    PracticeQuestionOut,
    PracticeSubmitRequest,
    PracticeSubmitResponse,
    PracticeAnswer,
    TopicPerformance,
    WrongAnswerDetail,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Time per question (seconds) when timed mode is on
SECONDS_PER_QUESTION = 60


# ─────────────────────────────────────────────────────────────
# Helper: build the list of previously-seen question IDs
# ─────────────────────────────────────────────────────────────

def _seen_question_ids(learning_progress: dict | None) -> set[str]:
    """Extract all question IDs the student has already answered."""
    if not learning_progress or not isinstance(learning_progress, dict):
        return set()
    practice_history: list = learning_progress.get("practice_history", [])
    seen: set[str] = set()
    for attempt in practice_history:
        if isinstance(attempt, dict):
            for ans in attempt.get("answers", []):
                if isinstance(ans, dict) and "question_id" in ans:
                    seen.add(str(ans["question_id"]))
    return seen


# ─────────────────────────────────────────────────────────────
# GET /student/practice/generate
# ─────────────────────────────────────────────────────────────

@router.get(
    "/student/practice/generate",
    response_model=PracticeGenerateResponse,
    summary="Generate a practice test for the student",
)
async def generate_practice_test(
    db: DBSession,
    current_user: User = Depends(get_current_user),
    topic_id: UUID | None = Query(None, description="Filter by topic; omit for Full Paper Mode"),
    num_questions: int = Query(25, ge=5, le=100),
    timed: bool = Query(False),
):
    """Generate a randomised set of MCQs, preferring questions the
    student has NOT answered before.  Falls back to already-seen
    questions when the pool is exhausted.
    """

    # ── Build base query (questions that have all 4 options + correct answer) ─
    base_filter = [
        Question.option_a.isnot(None),
        Question.option_b.isnot(None),
        Question.option_c.isnot(None),
        Question.option_d.isnot(None),
        Question.correct_answer.isnot(None),
    ]
    if topic_id:
        # Verify topic exists
        topic = await db.get(Topic, topic_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
        base_filter.append(Question.topic_id == topic_id)

    # ── Get previously-seen question IDs ────────────────────
    seen_ids = _seen_question_ids(current_user.learning_progress)

    # ── Try unseen questions first ──────────────────────────
    unseen_q = (
        select(Question)
        .where(*base_filter)
        .order_by(sqlfunc.random())
        .limit(num_questions)
    )
    if seen_ids:
        uuid_seen = [UUID(sid) for sid in seen_ids if len(sid) == 36]
        if uuid_seen:
            unseen_q = (
                select(Question)
                .where(*base_filter, ~Question.id.in_(uuid_seen))
                .order_by(sqlfunc.random())
                .limit(num_questions)
            )

    result = await db.execute(unseen_q)
    questions: list[Question] = list(result.scalars().all())

    # ── If not enough, backfill with seen questions ─────────
    if len(questions) < num_questions:
        remaining = num_questions - len(questions)
        already_picked = {q.id for q in questions}
        backfill_q = (
            select(Question)
            .where(*base_filter, ~Question.id.in_(already_picked))
            .order_by(sqlfunc.random())
            .limit(remaining)
        )
        backfill_result = await db.execute(backfill_q)
        questions.extend(backfill_result.scalars().all())

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions available for the selected criteria",
        )

    # ── Build topic name lookup ─────────────────────────────
    topic_ids_set = {q.topic_id for q in questions if q.topic_id}
    topic_name_map: dict[UUID, str] = {}
    if topic_ids_set:
        topic_rows = await db.execute(
            select(Topic.id, Topic.display_name).where(Topic.id.in_(topic_ids_set))
        )
        topic_name_map = {row.id: row.display_name for row in topic_rows.all()}

    # ── Build response ──────────────────────────────────────
    test_id = str(uuid4())
    time_limit = (len(questions) * SECONDS_PER_QUESTION) if timed else None

    question_out = [
        PracticeQuestionOut(
            id=q.id,
            question_text=q.question_text,
            option_a=q.option_a or "",
            option_b=q.option_b or "",
            option_c=q.option_c or "",
            option_d=q.option_d or "",
            topic_id=q.topic_id,
            topic_name=topic_name_map.get(q.topic_id, "General") if q.topic_id else "General",
            difficulty_score=q.difficulty_score or 0.5,
        )
        for q in questions
    ]

    return PracticeGenerateResponse(
        test_id=test_id,
        questions=question_out,
        total_questions=len(question_out),
        time_limit_seconds=time_limit,
    )


# ─────────────────────────────────────────────────────────────
# POST /student/practice/submit
# ─────────────────────────────────────────────────────────────

@router.post(
    "/student/practice/submit",
    response_model=PracticeSubmitResponse,
    summary="Submit practice test answers and get scored results",
)
async def submit_practice_test(
    body: PracticeSubmitRequest,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Score the student's answers, compute per-topic breakdown,
    and persist the attempt into ``learning_progress.practice_history``.
    """

    if not body.answers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No answers submitted",
        )

    # ── Fetch all referenced questions in one query ─────────
    q_ids = [a.question_id for a in body.answers]
    result = await db.execute(
        select(Question).where(Question.id.in_(q_ids))
    )
    q_map: dict[UUID, Question] = {q.id: q for q in result.scalars().all()}

    # ── Topic name lookup ───────────────────────────────────
    topic_ids_set = {q.topic_id for q in q_map.values() if q.topic_id}
    topic_name_map: dict[UUID, str] = {}
    if topic_ids_set:
        topic_rows = await db.execute(
            select(Topic.id, Topic.display_name).where(Topic.id.in_(topic_ids_set))
        )
        topic_name_map = {row.id: row.display_name for row in topic_rows.all()}

    # ── Score answers ───────────────────────────────────────
    score = 0
    wrong_answers: list[WrongAnswerDetail] = []
    topic_stats: dict[str, dict] = {}           # topic_name → {correct, total, topic_id}
    answer_records: list[dict] = []             # for learning_progress persistence

    for ans in body.answers:
        q = q_map.get(ans.question_id)
        if not q:
            continue  # skip unknown question IDs silently

        correct = q.correct_answer and ans.selected_answer.lower() == q.correct_answer.lower()
        if correct:
            score += 1

        # Determine topic name
        tname = topic_name_map.get(q.topic_id, "General") if q.topic_id else "General"

        # Aggregate per-topic stats
        if tname not in topic_stats:
            topic_stats[tname] = {"correct": 0, "total": 0, "topic_id": q.topic_id}
        topic_stats[tname]["total"] += 1
        if correct:
            topic_stats[tname]["correct"] += 1

        # Build wrong-answer detail
        if not correct:
            wrong_answers.append(
                WrongAnswerDetail(
                    question_id=q.id,
                    question_text=q.question_text,
                    option_a=q.option_a or "",
                    option_b=q.option_b or "",
                    option_c=q.option_c or "",
                    option_d=q.option_d or "",
                    selected_answer=ans.selected_answer,
                    correct_answer=q.correct_answer or "?",
                    topic_name=tname,
                    explanation=q.fact_extracted,
                )
            )

        # Record for persistence
        answer_records.append({
            "question_id": str(q.id),
            "selected": ans.selected_answer,
            "correct_answer": q.correct_answer,
            "is_correct": bool(correct),
        })

    total = len([a for a in body.answers if a.question_id in q_map])
    percentage = round((score / total * 100) if total > 0 else 0, 1)

    # ── Topic breakdown ─────────────────────────────────────
    topic_breakdown = [
        TopicPerformance(
            topic_id=info["topic_id"],
            topic_name=tname,
            correct=info["correct"],
            total=info["total"],
            percentage=round((info["correct"] / info["total"] * 100) if info["total"] > 0 else 0, 1),
        )
        for tname, info in sorted(topic_stats.items(), key=lambda x: x[1]["total"], reverse=True)
    ]

    # ── Persist to learning_progress ────────────────────────
    lp = dict(current_user.learning_progress or {})

    # practice_history: list of attempt dicts
    history: list = lp.get("practice_history", [])
    history.append({
        "test_id": body.test_id,
        "score": score,
        "total": total,
        "percentage": percentage,
        "time_taken_seconds": body.time_taken_seconds,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "answers": answer_records,
    })
    # Keep only last 50 attempts to avoid bloat
    if len(history) > 50:
        history = history[-50:]
    lp["practice_history"] = history

    # Per-topic cumulative stats
    topic_perf: dict = lp.get("topic_performance", {})
    for tname, info in topic_stats.items():
        tid = str(info["topic_id"]) if info["topic_id"] else "general"
        if tid not in topic_perf:
            topic_perf[tid] = {"topic_name": tname, "correct": 0, "total": 0}
        topic_perf[tid]["correct"] += info["correct"]
        topic_perf[tid]["total"] += info["total"]
        t = topic_perf[tid]["total"]
        topic_perf[tid]["percentage"] = round((topic_perf[tid]["correct"] / t * 100) if t > 0 else 0, 1)
    lp["topic_performance"] = topic_perf

    # Aggregate quick stat: total questions_practiced
    lp["questions_practiced"] = lp.get("questions_practiced", 0) + total

    current_user.learning_progress = lp
    db.add(current_user)
    await db.commit()

    return PracticeSubmitResponse(
        test_id=body.test_id,
        score=score,
        total=total,
        percentage=percentage,
        time_taken_seconds=body.time_taken_seconds,
        topic_breakdown=topic_breakdown,
        wrong_answers=wrong_answers,
    )
