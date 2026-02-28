"""
Topic Classification Service (GPT-4o-mini)
============================================
Classifies each parsed question into an existing topic or creates new ones.
"""

from __future__ import annotations

import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic import Topic
from app.services.openai.client import OpenAIService
from app.services.openai.models import OpenAICallType

logger = logging.getLogger(__name__)

# ── System prompt for classification ─────────────────────────
_CLASSIFY_SYSTEM_PROMPT = """\
You are an expert exam-question classifier for PPSC (Punjab Public Service Commission) Pakistan exams.

You will receive:
1. A JSON list of exam questions (each with question_number, question_text, and options).
2. A JSON list of existing topic names in our database.

For each question, classify it into the MOST appropriate existing topic.
If no existing topic fits, propose a NEW topic name.

Rules:
- Topic names should be concise, Title Case, max 5 words (e.g. "Pakistan History", "Islamic Studies", "General Science", "Computer Science", "Current Affairs", "English Grammar").
- Prefer existing topics whenever reasonably possible.
- Each question maps to exactly one topic.
- If the question is ambiguous or unclear, still give your best classification and set "confidence" to "low".

Return ONLY a JSON array (no markdown, no explanation):
[
  {"question_number": 1, "topic": "Pakistan History", "subtopic": "Independence Movement", "is_new_topic": false, "confidence": "high"},
  {"question_number": 2, "topic": "New Topic Name", "subtopic": null, "is_new_topic": true, "confidence": "medium"},
  ...
]
"""


async def classify_questions(
    db: AsyncSession,
    openai_svc: OpenAIService,
    questions: list[dict],
) -> list[dict]:
    """Classify a batch of questions using GPT-4o-mini.

    Parameters
    ----------
    db:
        DB session to fetch existing topics.
    openai_svc:
        The centralized OpenAI service.
    questions:
        List of dicts with ``question_number``, ``question_text``, ``option_a``..``option_d``.

    Returns
    -------
    list[dict]
        Classification results: ``question_number``, ``topic``, ``subtopic``,
        ``is_new_topic``, ``confidence``.
    """
    # Fetch existing topics
    result = await db.execute(select(Topic.name).order_by(Topic.name))
    existing_topics = [row[0] for row in result.all()]

    # Build the user prompt
    q_data = [
        {
            "question_number": q["question_number"],
            "question_text": q["question_text"],
            "options": {
                "A": q.get("option_a", ""),
                "B": q.get("option_b", ""),
                "C": q.get("option_c", ""),
                "D": q.get("option_d", ""),
            },
        }
        for q in questions
    ]

    user_prompt = (
        f"EXISTING TOPICS:\n{json.dumps(existing_topics)}\n\n"
        f"QUESTIONS TO CLASSIFY:\n{json.dumps(q_data, ensure_ascii=False)}"
    )

    # Call GPT-4o-mini (cheap, fast classification)
    raw = await openai_svc.classify(
        system_prompt=_CLASSIFY_SYSTEM_PROMPT,
        text=user_prompt,
        response_format={"type": "json_object"},
    )

    # Parse response — handle both {"classifications": [...]} and bare [...]
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            classifications = parsed.get("classifications", parsed.get("results", []))
        elif isinstance(parsed, list):
            classifications = parsed
        else:
            classifications = []
    except json.JSONDecodeError:
        logger.error("GPT classification returned invalid JSON: %s", raw[:500])
        classifications = []

    logger.info(
        "Classified %d/%d questions (%d existing topics in DB)",
        len(classifications), len(questions), len(existing_topics),
    )
    return classifications


async def resolve_topic_ids(
    db: AsyncSession,
    classifications: list[dict],
) -> dict[int, tuple[UUID, str | None]]:
    """Resolve classification results to topic IDs.

    Creates new topics in DB as needed.

    Returns
    -------
    dict[int, tuple[UUID, str | None]]
        ``{question_number: (topic_id, subtopic)}``
    """
    mapping: dict[int, tuple[UUID, str | None]] = {}

    # Cache existing topics
    result = await db.execute(select(Topic))
    topics_by_name: dict[str, Topic] = {t.name.lower(): t for t in result.scalars().all()}

    for cls in classifications:
        q_num = cls.get("question_number")
        topic_name = cls.get("topic", "").strip()
        subtopic = cls.get("subtopic")
        is_new = cls.get("is_new_topic", False)

        if not topic_name or q_num is None:
            continue

        topic_key = topic_name.lower()

        if topic_key in topics_by_name:
            topic = topics_by_name[topic_key]
        else:
            # Auto-create new topic
            topic = Topic(
                name=topic_name,
                display_name=topic_name,
                description=f"Auto-created during paper ingestion",
                trend_direction="new",
            )
            db.add(topic)
            await db.flush()
            await db.refresh(topic)
            topics_by_name[topic_key] = topic
            logger.info("Auto-created topic: %s (id=%s)", topic_name, topic.id)

        mapping[q_num] = (topic.id, subtopic)

    return mapping
