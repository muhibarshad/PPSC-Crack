"""
Story Document Generation Engine
===================================
Generates a comprehensive, flowing narrative educational document for a topic
once it accumulates 10+ questions in the database.

Uses GPT-4o to weave all extracted facts into a compelling story-style document
organised into canonical sections.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.models.topic import Topic
from app.crud.crud_topic import crud_topic
from app.services.openai.client import OpenAIService, get_openai_service
from app.services.openai.models import OpenAICallType

logger = logging.getLogger(__name__)

# ── Minimum questions required to trigger story generation ──
MIN_QUESTIONS_THRESHOLD = 10

# ── Canonical sections the GPT output must contain ──────────
STORY_SECTIONS = [
    "Introduction",
    "Core Foundations",
    "Historical Development",
    "Key Facts and Figures",
    "Relationships and Connections",
    "Recent Developments",
    "Exam Hotspots",
]

# ── System prompt — master educator persona ─────────────────
_STORY_SYSTEM_PROMPT = (
    "You are a master educator. Given the following list of facts extracted "
    "from government exam questions on the topic [{topic_name}], write a "
    "comprehensive, flowing, narrative educational document. Organize "
    "chronologically where applicable. Every single fact provided must appear "
    "somewhere in the document. Write as if telling a compelling story — use "
    "clear transitions, build from foundational concepts to advanced details, "
    "and make connections between related facts. Target length: detailed and "
    "complete. Do not use bullet points. Write in flowing paragraphs.\n\n"
    "Structure the output with these exact section headings "
    "(each on its own line, prefixed with ##):\n"
    "## Introduction\n"
    "## Core Foundations\n"
    "## Historical Development\n"
    "## Key Facts and Figures\n"
    "## Relationships and Connections\n"
    "## Recent Developments\n"
    "## Exam Hotspots\n"
)


class StoryEngine:
    """Stateless service — generates story documents for topics."""

    def __init__(self, db: AsyncSession, openai_svc: OpenAIService | None = None) -> None:
        self.db = db
        self.openai = openai_svc or get_openai_service()

    # ═════════════════════════════════════════════════════════
    # Public API
    # ═════════════════════════════════════════════════════════

    async def generate(
        self,
        topic_id: UUID,
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        """Generate (or regenerate) the story document for a topic.

        Parameters
        ----------
        topic_id:
            The topic to generate a story for.
        force:
            If ``True``, regenerate even when a story already exists
            or the topic has < 10 questions.

        Returns
        -------
        dict with keys: status, topic_id, topic_name, word_count, sections
        """
        topic = await crud_topic.get_or_404(self.db, id=topic_id)

        # ── Guard: enough questions? ────────────────────────
        question_count = await self._count_topic_questions(topic_id)
        if question_count < MIN_QUESTIONS_THRESHOLD and not force:
            logger.info(
                "Topic %s (%s) has only %d questions — skipping story generation (need %d).",
                topic_id, topic.name, question_count, MIN_QUESTIONS_THRESHOLD,
            )
            return {
                "status": "skipped",
                "topic_id": str(topic_id),
                "topic_name": topic.name,
                "reason": f"Only {question_count} questions (need {MIN_QUESTIONS_THRESHOLD}+).",
                "question_count": question_count,
            }

        # ── Collect facts ───────────────────────────────────
        facts = await self._collect_facts(topic_id)
        if not facts:
            logger.warning("Topic %s has questions but no extracted facts.", topic_id)
            return {
                "status": "skipped",
                "topic_id": str(topic_id),
                "topic_name": topic.name,
                "reason": "No extracted facts available.",
                "question_count": question_count,
            }

        # ── Build prompt ────────────────────────────────────
        system_prompt = _STORY_SYSTEM_PROMPT.replace("{topic_name}", topic.display_name)
        user_prompt = self._build_user_prompt(topic, facts, question_count)

        # ── Call GPT-4o ─────────────────────────────────────
        logger.info(
            "Generating story for topic=%s (%s) with %d facts …",
            topic_id, topic.display_name, len(facts),
        )
        story_text = await self.openai.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            call_type=OpenAICallType.STORY_GENERATION,
            temperature=0.8,
            max_tokens=4096,
        )

        # ── Compute word count ──────────────────────────────
        word_count = len(story_text.split())

        # ── Persist to DB ───────────────────────────────────
        await crud_topic.update_story(
            self.db,
            id=topic_id,
            story_document=story_text,
            word_count=word_count,
        )

        logger.info(
            "Story generated for topic=%s (%s): %d words, %d sections.",
            topic_id, topic.display_name, word_count,
            sum(1 for s in STORY_SECTIONS if f"## {s}" in story_text),
        )

        return {
            "status": "generated",
            "topic_id": str(topic_id),
            "topic_name": topic.display_name,
            "word_count": word_count,
            "question_count": question_count,
            "fact_count": len(facts),
            "sections_found": [s for s in STORY_SECTIONS if f"## {s}" in story_text],
        }

    async def check_and_generate_for_topic(
        self,
        topic_id: UUID,
    ) -> dict[str, Any]:
        """Check whether a topic has reached the threshold and generate if so.

        Intended to be called after question ingestion to auto-trigger
        story generation when the topic hits 10+ questions.
        """
        question_count = await self._count_topic_questions(topic_id)
        if question_count < MIN_QUESTIONS_THRESHOLD:
            return {
                "status": "below_threshold",
                "topic_id": str(topic_id),
                "question_count": question_count,
                "threshold": MIN_QUESTIONS_THRESHOLD,
            }
        return await self.generate(topic_id)

    async def batch_generate_eligible(self) -> list[dict[str, Any]]:
        """Scan all topics and generate stories for any with 10+ questions
        that don't yet have a story document.

        Useful for back-filling stories after initial data load.
        """
        eligible = await self._find_eligible_topics()
        results: list[dict[str, Any]] = []

        for topic_id, topic_name, q_count in eligible:
            logger.info("Batch: generating story for %s (%d questions) …", topic_name, q_count)
            try:
                result = await self.generate(topic_id, force=True)
                results.append(result)
            except Exception:
                logger.exception("Batch: story generation failed for topic=%s", topic_id)
                results.append({
                    "status": "error",
                    "topic_id": str(topic_id),
                    "topic_name": topic_name,
                })

        return results

    # ═════════════════════════════════════════════════════════
    # Private helpers
    # ═════════════════════════════════════════════════════════

    async def _count_topic_questions(self, topic_id: UUID) -> int:
        """Return the number of questions linked to a topic."""
        result = await self.db.execute(
            select(func.count(Question.id)).where(Question.topic_id == topic_id)
        )
        return result.scalar_one()

    async def _collect_facts(self, topic_id: UUID) -> list[dict[str, Any]]:
        """Gather all extracted facts for a topic's questions."""
        result = await self.db.execute(
            select(
                Question.question_number,
                Question.question_text,
                Question.fact_extracted,
                Question.year_appeared,
                Question.correct_answer,
                Question.is_repeated,
                Question.repeat_count,
            )
            .where(Question.topic_id == topic_id)
            .where(Question.fact_extracted.isnot(None))
            .order_by(Question.year_appeared.asc().nulls_last(), Question.question_number.asc())
        )
        rows = result.all()
        return [
            {
                "question_number": r.question_number,
                "question_text": r.question_text,
                "fact": r.fact_extracted,
                "year": r.year_appeared,
                "correct_answer": r.correct_answer,
                "is_repeated": r.is_repeated,
                "repeat_count": r.repeat_count,
            }
            for r in rows
        ]

    def _build_user_prompt(
        self,
        topic: Topic,
        facts: list[dict[str, Any]],
        question_count: int,
    ) -> str:
        """Assemble the user-facing prompt with all facts."""
        lines = [
            f"Topic: {topic.display_name}",
            f"Total questions in database: {question_count}",
            f"Total facts extracted: {len(facts)}",
            "",
            "=== EXTRACTED FACTS ===",
        ]

        for i, f in enumerate(facts, 1):
            year_tag = f" (Year: {f['year']})" if f.get("year") else ""
            repeat_tag = f" [REPEATED {f['repeat_count']}x]" if f.get("is_repeated") else ""
            lines.append(f"{i}. {f['fact']}{year_tag}{repeat_tag}")

        lines.append("")
        lines.append(
            "IMPORTANT: Every single fact listed above MUST appear somewhere "
            "in the narrative. Do not skip any."
        )

        return "\n".join(lines)

    async def _find_eligible_topics(
        self,
    ) -> list[tuple[UUID, str, int]]:
        """Find topics with 10+ questions and no existing story."""
        result = await self.db.execute(
            select(
                Topic.id,
                Topic.display_name,
                func.count(Question.id).label("q_count"),
            )
            .outerjoin(Question, Question.topic_id == Topic.id)
            .where(Topic.story_document.is_(None))
            .group_by(Topic.id, Topic.display_name)
            .having(func.count(Question.id) >= MIN_QUESTIONS_THRESHOLD)
            .order_by(func.count(Question.id).desc())
        )
        return [(row.id, row.display_name, row.q_count) for row in result.all()]


# ═════════════════════════════════════════════════════════════
# Module-level convenience (matches pattern_engine.py style)
# ═════════════════════════════════════════════════════════════

async def run_story_generation(
    db: AsyncSession,
    topic_id: UUID,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Convenience wrapper — creates engine and runs generation."""
    engine = StoryEngine(db)
    return await engine.generate(topic_id, force=force)


async def run_batch_story_generation(
    db: AsyncSession,
) -> list[dict[str, Any]]:
    """Convenience wrapper — batch-generate all eligible stories."""
    engine = StoryEngine(db)
    return await engine.batch_generate_eligible()
