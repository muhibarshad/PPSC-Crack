"""
Student Topic Story Reader API
================================
GET  /api/v1/student/topics/{topic_id}/story    → immersive story reader data
POST /api/v1/student/topics/{topic_id}/progress → save reading progress
POST /api/v1/student/topics/{topic_id}/quiz     → generate section quiz (GPT-4o)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.dependencies import DBSession, OpenAI, get_current_user
from app.models.question import Question
from app.models.topic import Topic
from app.models.user import User
from app.services.openai.models import OpenAICallType
from app.schemas.story_reader import (
    BookmarkData,
    GenerateQuizRequest,
    GenerateQuizResponse,
    HighFreqFact,
    InlineNote,
    QuizOption,
    QuizQuestion,
    SaveProgressRequest,
    SaveProgressResponse,
    SectionQuiz,
    StoryReaderResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

HIGH_FREQ_THRESHOLD = 3  # facts appearing in 3+ papers


# ─────────────────────────────────────────────────────────────
# GET /student/topics/{topic_id}/story — immersive reader data
# ─────────────────────────────────────────────────────────────

@router.get(
    "/student/topics/{topic_id}/story",
    response_model=StoryReaderResponse,
    summary="Get story reader data for immersive reading experience",
)
async def get_story_reader(
    topic_id: UUID,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Return the full story document along with high-frequency facts,
    saved bookmarks/notes, and reading progress for the current student.
    """
    # ── Fetch topic ──────────────────────────────────────────
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic {topic_id} not found",
        )

    # ── High-frequency facts (repeat_count >= 3) ────────────
    hf_q = (
        select(Question.fact_extracted, Question.repeat_count, Question.question_text)
        .where(
            Question.topic_id == topic_id,
            Question.repeat_count >= HIGH_FREQ_THRESHOLD,
            Question.fact_extracted.isnot(None),
        )
        .order_by(Question.repeat_count.desc())
    )
    hf_rows = (await db.execute(hf_q)).all()

    high_freq_facts = [
        HighFreqFact(
            fact_text=row.fact_extracted,
            repeat_count=row.repeat_count,
            question_text=row.question_text,
        )
        for row in hf_rows
    ]

    # ── Student reading progress from learning_progress JSON ─
    lp = current_user.learning_progress or {}
    tid = str(topic_id)
    topic_progress = lp.get(tid, {}) if isinstance(lp, dict) else {}
    story_data = topic_progress.get("story_reader", {}) if isinstance(topic_progress, dict) else {}

    reading_progress = float(story_data.get("reading_progress", 0.0))
    sections_unlocked = int(story_data.get("sections_unlocked", 1))

    bookmarks = [
        BookmarkData(**b)
        for b in story_data.get("bookmarks", [])
        if isinstance(b, dict)
    ]
    notes = [
        InlineNote(**n)
        for n in story_data.get("notes", [])
        if isinstance(n, dict)
    ]
    quizzes = [
        SectionQuiz(**q)
        for q in story_data.get("quizzes", [])
        if isinstance(q, dict)
    ]

    return StoryReaderResponse(
        topic_id=topic.id,
        topic_name=topic.name,
        display_name=topic.display_name,
        story_document=topic.story_document,
        story_word_count=topic.story_word_count,
        story_last_updated=topic.story_last_updated,
        total_questions=topic.total_questions,
        frequency_score=topic.frequency_score,
        color_hex=topic.color_hex,
        icon=topic.icon,
        high_freq_facts=high_freq_facts,
        reading_progress=reading_progress,
        sections_unlocked=sections_unlocked,
        bookmarks=bookmarks,
        notes=notes,
        quizzes=quizzes,
    )


# ─────────────────────────────────────────────────────────────
# POST /student/topics/{topic_id}/progress — save reading progress
# ─────────────────────────────────────────────────────────────

@router.post(
    "/student/topics/{topic_id}/progress",
    response_model=SaveProgressResponse,
    summary="Save reading progress for a topic story",
)
async def save_story_progress(
    topic_id: UUID,
    body: SaveProgressRequest,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Persist the student's reading progress, bookmarks, and notes
    into the User.learning_progress JSON column.
    """
    # Verify topic exists
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic {topic_id} not found",
        )

    tid = str(topic_id)
    lp = dict(current_user.learning_progress or {})

    # Initialise topic entry if missing
    if tid not in lp or not isinstance(lp[tid], dict):
        lp[tid] = {}

    # Update story reader sub-key
    lp[tid]["story_reader"] = {
        "reading_progress": body.reading_progress,
        "sections_unlocked": body.sections_unlocked,
        "bookmarks": [b.model_dump() for b in body.bookmarks],
        "notes": [n.model_dump() for n in body.notes],
    }

    # Mark completed if applicable
    if body.completed:
        lp[tid]["completed"] = True
        lp[tid]["completed_at"] = datetime.now(timezone.utc).isoformat()
        # Add to stories_read list
        stories_read = set(lp.get("stories_read", []))
        stories_read.add(tid)
        lp["stories_read"] = list(stories_read)

    # Record session date for streak tracking
    today = datetime.now(timezone.utc).date().isoformat()
    session_dates = lp.get("session_dates", [])
    if today not in session_dates:
        session_dates.append(today)
    lp["session_dates"] = session_dates

    current_user.learning_progress = lp
    db.add(current_user)
    await db.commit()

    return SaveProgressResponse(
        topic_id=topic_id,
        saved=True,
        message="Reading progress saved successfully.",
    )


# ─────────────────────────────────────────────────────────────
# POST /student/topics/{topic_id}/quiz — generate section quiz
# ─────────────────────────────────────────────────────────────

QUIZ_SYSTEM_PROMPT = """You are an expert exam question writer for PPSC (Punjab Public Service Commission) exams in Pakistan.
Given a section of educational text, generate exactly {count} multiple-choice questions (MCQs) that test key facts from the content.

Rules:
1. Each question must have exactly 4 options (A, B, C, D).
2. Exactly one option must be correct.
3. Questions should test factual recall, not opinion.
4. Include a brief explanation for the correct answer.
5. Questions should be clear, concise, and exam-style.

Return valid JSON array:
[
  {{
    "question": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "correct_answer": "A",
    "explanation": "..."
  }}
]

Return ONLY the JSON array, no other text."""


@router.post(
    "/student/topics/{topic_id}/quiz",
    response_model=GenerateQuizResponse,
    summary="Generate MCQ quiz for a story section using GPT-4o",
)
async def generate_section_quiz(
    topic_id: UUID,
    body: GenerateQuizRequest,
    db: DBSession,
    openai: OpenAI,
    current_user: User = Depends(get_current_user),
):
    """Use GPT-4o to generate 2-3 MCQs from the given section text.
    Saves the generated quiz to the user's progress for caching.
    """
    # Verify topic
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic {topic_id} not found",
        )

    # Trim section text to reasonable length
    section_text = body.section_text[:3000]
    num_questions = 3 if len(section_text) > 500 else 2

    prompt = QUIZ_SYSTEM_PROMPT.format(count=num_questions)

    try:
        raw = await openai.chat(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Generate {num_questions} MCQs from this section:\n\n{section_text}"},
            ],
            call_type=OpenAICallType.MCQ_GENERATION,
            model="gpt-4o",
            temperature=0.3,
            max_tokens=1500,
        )

        # Parse JSON from response (handle potential markdown wrapping)
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        items = json.loads(raw)

    except Exception as e:
        logger.error(f"Quiz generation failed for topic {topic_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate quiz. Please try again.",
        )

    # Convert to schema
    quiz_questions = []
    for i, item in enumerate(items[:num_questions]):
        opts = item.get("options", {})
        quiz_questions.append(
            QuizQuestion(
                id=str(uuid4())[:8],
                question=item.get("question", ""),
                options=[
                    QuizOption(label=k, text=v) for k, v in opts.items()
                ],
                correct_answer=item.get("correct_answer", "A"),
                explanation=item.get("explanation", ""),
            )
        )

    quiz = SectionQuiz(
        section_index=body.section_index,
        questions=quiz_questions,
    )

    # Cache quiz in user progress
    tid = str(topic_id)
    lp = dict(current_user.learning_progress or {})
    if tid not in lp or not isinstance(lp[tid], dict):
        lp[tid] = {}
    story_data = lp[tid].get("story_reader", {})
    existing_quizzes = story_data.get("quizzes", [])
    # Replace quiz for same section if exists
    existing_quizzes = [q for q in existing_quizzes if q.get("section_index") != body.section_index]
    existing_quizzes.append(quiz.model_dump())
    story_data["quizzes"] = existing_quizzes
    lp[tid]["story_reader"] = story_data
    current_user.learning_progress = lp
    db.add(current_user)
    await db.commit()

    return GenerateQuizResponse(
        topic_id=topic_id,
        section_index=body.section_index,
        quiz=quiz,
    )
