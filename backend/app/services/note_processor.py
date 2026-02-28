"""
Admin Note Processing Service
================================
AI pipeline that processes raw admin-contributed notes:

1. **Topic identification** — GPT-4o reads raw_content and identifies
   which existing topic(s) it belongs to.
2. **Fact extraction** — extracts useful, exam-relevant facts.
3. **Position-in-story** — determines which canonical story section the
   note content belongs to (returns section index).
4. **Embedding generation** — text-embedding-3-small (1 536 dims).
5. **Queue incremental story update** — fires the Celery task that
   surgically patches the assigned topic's story document.
6. **Mark processed** — sets ``processed=True`` on the AdminNote row.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_admin_note import crud_admin_note
from app.models.admin_note import AdminNote
from app.models.topic import Topic
from app.services.openai.client import OpenAIService, get_openai_service
from app.services.openai.models import OpenAICallType
from app.services.story_engine import STORY_SECTIONS

logger = logging.getLogger(__name__)

# ── Section name → index mapping ────────────────────────────
_SECTION_INDEX = {name.lower(): idx for idx, name in enumerate(STORY_SECTIONS)}

# ── System prompt — topic identification + fact extraction ───
_NOTE_PROCESSING_SYSTEM_PROMPT = """\
You are an expert education analyst working for a Pakistan government exam preparation platform.
You are given a raw admin note and a list of existing topics in the database.

Your job:
1. **Identify the topic**: Pick the SINGLE most relevant topic from the provided list.
   If none match, return topic_name as "unknown".
2. **Extract facts**: Pull out every useful, exam-relevant factual statement from the note.
   Each fact should be a concise, standalone statement.
3. **Determine story section**: Based on the content, decide which section of the topic's
   story document this note best fits into. Return the section name from this list:
   {sections}

Respond ONLY with valid JSON (no markdown fences):
{{
  "topic_name": "<exact topic name from the provided list, or 'unknown'>",
  "facts": ["fact 1", "fact 2", ...],
  "story_section": "<section name from the list above>"
}}
"""

# ═════════════════════════════════════════════════════════════
# Note Processor
# ═════════════════════════════════════════════════════════════


class NoteProcessor:
    """Processes a single AdminNote through the full AI pipeline."""

    def __init__(
        self,
        db: AsyncSession,
        openai_svc: OpenAIService | None = None,
    ) -> None:
        self.db = db
        self.openai = openai_svc or get_openai_service()

    async def process_note(self, note_id: UUID) -> dict[str, Any]:
        """Run the full processing pipeline for an admin note.

        Returns
        -------
        dict
            Summary with keys: status, topic_name, topic_id, facts_count,
            story_section, position_in_story.
        """
        # ── 1. Load the note ─────────────────────────────────
        note = await crud_admin_note.get_or_404(self.db, id=note_id)

        if note.processed:
            logger.info("Note %s already processed — skipping", note_id)
            return {"status": "already_processed", "note_id": str(note_id)}

        # ── 2. Fetch all existing topics ─────────────────────
        result = await self.db.execute(
            select(Topic.name, Topic.id).order_by(Topic.name)
        )
        topics_map: dict[str, UUID] = {
            row.name: row.id for row in result.all()
        }
        topic_names = list(topics_map.keys())

        if not topic_names:
            logger.warning("No topics in DB — cannot assign note %s", note_id)
            return {"status": "no_topics", "note_id": str(note_id)}

        # ── 3. GPT-4o: identify topic, extract facts, find section
        sections_str = ", ".join(f'"{s}"' for s in STORY_SECTIONS)
        system_prompt = _NOTE_PROCESSING_SYSTEM_PROMPT.format(sections=sections_str)

        user_prompt = (
            f"## Existing Topics\n{json.dumps(topic_names)}\n\n"
            f"## Raw Admin Note\n{note.raw_content}"
        )

        raw_response = await self.openai.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            call_type=OpenAICallType.PAPER_PROCESSING,
            temperature=0.2,
            max_tokens=2000,
        )

        # ── 4. Parse GPT response ───────────────────────────
        parsed = self._parse_response(raw_response)
        topic_name: str = parsed.get("topic_name", "unknown")
        facts: list[str] = parsed.get("facts", [])
        story_section: str = parsed.get("story_section", "Exam Hotspots")

        # Resolve topic
        topic_id: UUID | None = topics_map.get(topic_name)
        if topic_id is None:
            # Try case-insensitive match
            for db_name, db_id in topics_map.items():
                if db_name.lower() == topic_name.lower():
                    topic_id = db_id
                    topic_name = db_name
                    break

        # Resolve section index
        position = _SECTION_INDEX.get(story_section.lower(), len(STORY_SECTIONS) - 1)

        logger.info(
            "Note %s → topic=%s (%s), facts=%d, section=%s (pos=%d)",
            note_id, topic_name, topic_id, len(facts), story_section, position,
        )

        # ── 5. Generate embedding from raw content ───────────
        embedding = await self.openai.embed(note.raw_content)

        # ── 6. Build processed content ───────────────────────
        processed_content = "\n".join(f"• {f}" for f in facts) if facts else note.raw_content

        # ── 7. Persist: mark processed + embedding ───────────
        await crud_admin_note.mark_processed(
            self.db,
            id=note_id,
            processed_content=processed_content,
            topic_id=topic_id,
            position=position,
        )

        if embedding:
            await crud_admin_note.set_embedding(
                self.db, id=note_id, embedding=embedding
            )

        await self.db.commit()

        # ── 8. Queue incremental story update ────────────────
        story_task_id: str | None = None
        if topic_id and facts:
            try:
                from app.tasks.story_generation import incremental_facts_update
                task = incremental_facts_update.apply_async(
                    args=[str(topic_id)],
                    kwargs={"fact_texts": facts},
                    queue="ai_pipeline",
                )
                story_task_id = task.id
                logger.info(
                    "Queued incremental story update (task=%s) for topic=%s with %d facts",
                    story_task_id, topic_id, len(facts),
                )
            except Exception:
                logger.exception("Failed to queue story update for note %s", note_id)

        return {
            "status": "processed",
            "note_id": str(note_id),
            "topic_name": topic_name,
            "topic_id": str(topic_id) if topic_id else None,
            "facts_count": len(facts),
            "facts": facts,
            "story_section": story_section,
            "position_in_story": position,
            "story_task_id": story_task_id,
        }

    # ─────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _parse_response(raw: str) -> dict[str, Any]:
        """Parse the GPT JSON response, handling common formatting issues."""
        text = raw.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (fences)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse GPT response as JSON: %s", text[:200])
            return {"topic_name": "unknown", "facts": [], "story_section": "Exam Hotspots"}


# ═════════════════════════════════════════════════════════════
# Convenience Functions
# ═════════════════════════════════════════════════════════════

async def run_note_processing(
    db: AsyncSession,
    note_id: UUID,
    openai_svc: OpenAIService | None = None,
) -> dict[str, Any]:
    """Convenience wrapper: process a single admin note."""
    processor = NoteProcessor(db, openai_svc)
    return await processor.process_note(note_id)


async def run_batch_note_processing(
    db: AsyncSession,
    limit: int = 50,
    openai_svc: OpenAIService | None = None,
) -> list[dict[str, Any]]:
    """Process all unprocessed notes (up to *limit*)."""
    unprocessed = await crud_admin_note.get_unprocessed(db, limit=limit)
    if not unprocessed:
        logger.info("No unprocessed admin notes found")
        return []

    processor = NoteProcessor(db, openai_svc)
    results: list[dict[str, Any]] = []

    for note in unprocessed:
        try:
            result = await processor.process_note(note.id)
            results.append(result)
        except Exception:
            logger.exception("Error processing note %s", note.id)
            results.append({"status": "error", "note_id": str(note.id)})

    return results
