"""
Incremental Story Document Update Engine
==========================================
After each paper ingestion, surgically updates only the affected sections
of an existing story document by embedding new facts and comparing them
against section embeddings via cosine similarity.

**This never regenerates the full document** — it patches individual
sections with a targeted GPT-4o call.

Flow
----
1. Collect new facts from the ingested paper for a given topic.
2. Parse the existing story document into its canonical sections.
3. Embed each new fact and each section using text-embedding-3-small.
4. For every new fact, find the best-matching section (cosine similarity).
5. For each affected section, call GPT-4o with a surgical update prompt.
6. Replace old section text with the updated section text.
7. Persist the updated story document, word count, and timestamp.
"""

from __future__ import annotations

import logging
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_topic import crud_topic
from app.models.question import Question
from app.models.topic import Topic
from app.services.openai.client import OpenAIService, get_openai_service
from app.services.openai.models import OpenAICallType
from app.services.story_engine import STORY_SECTIONS, MIN_QUESTIONS_THRESHOLD

logger = logging.getLogger(__name__)

# ── Similarity threshold: below this → "Exam Hotspots" catch-all ─
SECTION_MATCH_THRESHOLD = 0.30

# ── Section-update system prompt ─────────────────────────────
_SECTION_UPDATE_SYSTEM_PROMPT = (
    "You are a master educator updating a section of a comprehensive educational document "
    "on the topic [{topic_name}]. You write in flowing paragraphs — never use bullet points. "
    "Maintain the existing narrative style, tone, and flow. Incorporate the new fact(s) "
    "naturally, placing them where they fit chronologically or thematically. "
    "Do NOT remove or alter any existing information. "
    "Return ONLY the updated section text (no heading, no preamble)."
)

# ── New-section creation system prompt ───────────────────────
_NEW_SECTION_SYSTEM_PROMPT = (
    "You are a master educator. Write a new section for a comprehensive educational document "
    "on the topic [{topic_name}]. Write in flowing paragraphs — never use bullet points. "
    "The section heading is [{section_name}]. Incorporate the following fact(s) into a "
    "coherent, narrative passage that connects to the broader topic. "
    "Return ONLY the section body text (no heading, no preamble)."
)


# ═════════════════════════════════════════════════════════════
# Section Parser
# ═════════════════════════════════════════════════════════════

def parse_story_sections(story_document: str) -> dict[str, str]:
    """Split a story document into {section_name: section_body} by ``## Heading``.

    Returns an OrderedDict-like dict preserving insertion order.
    Unrecognised headings are kept as-is.
    """
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in story_document.splitlines():
        heading_match = re.match(r"^##\s+(.+)$", line.strip())
        if heading_match:
            # Save the previous section
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = heading_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save the last section
    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def reassemble_story(sections: dict[str, str]) -> str:
    """Reconstruct the full story document from section dict."""
    parts: list[str] = []
    for heading, body in sections.items():
        parts.append(f"## {heading}")
        parts.append("")
        parts.append(body)
        parts.append("")
    return "\n".join(parts).strip() + "\n"


# ═════════════════════════════════════════════════════════════
# Cosine Similarity
# ═════════════════════════════════════════════════════════════

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ═════════════════════════════════════════════════════════════
# Incremental Story Update Engine
# ═════════════════════════════════════════════════════════════

class IncrementalStoryEngine:
    """Surgically updates only affected sections of a story document."""

    def __init__(self, db: AsyncSession, openai_svc: OpenAIService | None = None) -> None:
        self.db = db
        self.openai = openai_svc or get_openai_service()

    # ─────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────

    async def update_from_paper(
        self,
        topic_id: UUID,
        paper_id: UUID,
    ) -> dict[str, Any]:
        """Incrementally update a topic's story document with new facts
        from a specific paper.

        Parameters
        ----------
        topic_id
            The topic whose story document to update.
        paper_id
            The paper whose newly-ingested questions provide the facts.

        Returns
        -------
        dict  —  status, sections_updated, new_facts_count, word_count, etc.
        """
        topic = await crud_topic.get_or_404(self.db, id=topic_id)

        # ── Guard: story must already exist ─────────────────
        if not topic.story_document:
            logger.info(
                "Topic %s (%s) has no story document — falling back to full generation.",
                topic_id, topic.display_name,
            )
            return {
                "status": "no_story",
                "topic_id": str(topic_id),
                "topic_name": topic.display_name,
                "reason": "No existing story document to update. Use full generation first.",
            }

        # ── Step 1: Collect new facts from this paper ───────
        new_facts = await self._get_paper_facts(topic_id, paper_id)
        if not new_facts:
            logger.info(
                "No new facts from paper=%s for topic=%s — nothing to update.",
                paper_id, topic_id,
            )
            return {
                "status": "no_new_facts",
                "topic_id": str(topic_id),
                "topic_name": topic.display_name,
                "paper_id": str(paper_id),
                "new_facts_count": 0,
            }

        # ── Step 2: Parse existing story into sections ──────
        sections = parse_story_sections(topic.story_document)
        if not sections:
            logger.warning(
                "Failed to parse sections from topic=%s story — falling back to full generation.",
                topic_id,
            )
            return {
                "status": "parse_error",
                "topic_id": str(topic_id),
                "topic_name": topic.display_name,
                "reason": "Could not parse sections from existing story document.",
            }

        # ── Step 3: Embed facts + sections ──────────────────
        fact_texts = [f["fact"] for f in new_facts]
        section_names = list(sections.keys())
        section_texts = [sections[name] for name in section_names]

        # Build embedding texts: section_name + first 500 chars of body
        section_embed_texts = [
            f"{name}: {text[:500]}" for name, text in zip(section_names, section_texts)
        ]

        all_texts = fact_texts + section_embed_texts
        logger.info(
            "Embedding %d new facts + %d sections for topic=%s …",
            len(fact_texts), len(section_names), topic_id,
        )
        all_embeddings = await self.openai.embed(all_texts)

        fact_embeddings = all_embeddings[: len(fact_texts)]
        section_embeddings = all_embeddings[len(fact_texts) :]

        # ── Step 4: Route each fact to its best section ─────
        section_fact_map: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for fact, fact_emb in zip(new_facts, fact_embeddings):
            best_section = None
            best_score = -1.0

            for sec_name, sec_emb in zip(section_names, section_embeddings):
                score = _cosine_similarity(fact_emb, sec_emb)
                if score > best_score:
                    best_score = score
                    best_section = sec_name

            # If similarity is too low, route to "Exam Hotspots" as catch-all
            if best_score < SECTION_MATCH_THRESHOLD:
                target = "Exam Hotspots" if "Exam Hotspots" in sections else section_names[-1]
            else:
                target = best_section  # type: ignore[assignment]

            section_fact_map[target].append({
                **fact,
                "similarity_score": round(best_score, 4),
                "matched_section": target,
            })

        logger.info(
            "Fact routing for topic=%s: %s",
            topic_id,
            {k: len(v) for k, v in section_fact_map.items()},
        )

        # ── Step 5: Update each affected section via GPT-4o ─
        updated_sections: list[str] = []
        for section_name, facts_for_section in section_fact_map.items():
            old_text = sections.get(section_name, "")
            new_text = await self._update_section(
                topic_name=topic.display_name,
                section_name=section_name,
                old_section_text=old_text,
                new_facts=facts_for_section,
            )
            sections[section_name] = new_text
            updated_sections.append(section_name)

        # ── Step 6: Reassemble and persist ──────────────────
        updated_story = reassemble_story(sections)
        word_count = len(updated_story.split())

        await crud_topic.update_story(
            self.db,
            id=topic_id,
            story_document=updated_story,
            word_count=word_count,
        )

        logger.info(
            "Incremental story update complete for topic=%s: "
            "%d facts incorporated, %d sections updated, %d words.",
            topic_id, len(new_facts), len(updated_sections), word_count,
        )

        return {
            "status": "updated",
            "topic_id": str(topic_id),
            "topic_name": topic.display_name,
            "paper_id": str(paper_id),
            "new_facts_count": len(new_facts),
            "sections_updated": updated_sections,
            "word_count": word_count,
            "fact_routing": {
                section: [
                    {"fact": f["fact"], "similarity": f["similarity_score"]}
                    for f in facts
                ]
                for section, facts in section_fact_map.items()
            },
        }

    async def update_from_facts(
        self,
        topic_id: UUID,
        fact_texts: list[str],
    ) -> dict[str, Any]:
        """Incrementally update a topic's story document with an explicit
        list of fact strings (not tied to a specific paper).

        Useful for admin-driven updates or reprocessing.
        """
        topic = await crud_topic.get_or_404(self.db, id=topic_id)

        if not topic.story_document:
            return {
                "status": "no_story",
                "topic_id": str(topic_id),
                "topic_name": topic.display_name,
                "reason": "No existing story document to update.",
            }

        if not fact_texts:
            return {
                "status": "no_new_facts",
                "topic_id": str(topic_id),
                "new_facts_count": 0,
            }

        # Build fact dicts in the same shape
        new_facts = [{"fact": ft, "year": None, "is_repeated": False} for ft in fact_texts]

        sections = parse_story_sections(topic.story_document)
        if not sections:
            return {
                "status": "parse_error",
                "topic_id": str(topic_id),
                "reason": "Could not parse sections from existing story.",
            }

        # Embed
        section_names = list(sections.keys())
        section_embed_texts = [
            f"{name}: {sections[name][:500]}" for name in section_names
        ]
        all_texts = fact_texts + section_embed_texts
        all_embeddings = await self.openai.embed(all_texts)

        fact_embeddings = all_embeddings[: len(fact_texts)]
        section_embeddings = all_embeddings[len(fact_texts) :]

        # Route facts
        section_fact_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for fact, fact_emb in zip(new_facts, fact_embeddings):
            best_section = None
            best_score = -1.0
            for sec_name, sec_emb in zip(section_names, section_embeddings):
                score = _cosine_similarity(fact_emb, sec_emb)
                if score > best_score:
                    best_score = score
                    best_section = sec_name

            target = (
                best_section
                if best_score >= SECTION_MATCH_THRESHOLD
                else ("Exam Hotspots" if "Exam Hotspots" in sections else section_names[-1])
            )
            section_fact_map[target].append({  # type: ignore[index]
                **fact,
                "similarity_score": round(best_score, 4),
            })

        # Update each affected section
        updated_sections: list[str] = []
        for section_name, facts_for_section in section_fact_map.items():
            old_text = sections.get(section_name, "")
            new_text = await self._update_section(
                topic_name=topic.display_name,
                section_name=section_name,
                old_section_text=old_text,
                new_facts=facts_for_section,
            )
            sections[section_name] = new_text
            updated_sections.append(section_name)

        # Persist
        updated_story = reassemble_story(sections)
        word_count = len(updated_story.split())
        await crud_topic.update_story(
            self.db, id=topic_id, story_document=updated_story, word_count=word_count,
        )

        return {
            "status": "updated",
            "topic_id": str(topic_id),
            "topic_name": topic.display_name,
            "new_facts_count": len(fact_texts),
            "sections_updated": updated_sections,
            "word_count": word_count,
        }

    # ─────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────

    async def _get_paper_facts(
        self, topic_id: UUID, paper_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get extracted facts for questions from a specific paper + topic."""
        result = await self.db.execute(
            select(
                Question.id,
                Question.question_number,
                Question.fact_extracted,
                Question.year_appeared,
                Question.is_repeated,
                Question.repeat_count,
            )
            .where(Question.paper_id == paper_id)
            .where(Question.topic_id == topic_id)
            .where(Question.fact_extracted.isnot(None))
            .where(Question.fact_extracted != "")
            .order_by(Question.question_number.asc())
        )
        return [
            {
                "question_id": str(row.id),
                "question_number": row.question_number,
                "fact": row.fact_extracted,
                "year": row.year_appeared,
                "is_repeated": row.is_repeated,
                "repeat_count": row.repeat_count,
            }
            for row in result.all()
        ]

    async def _update_section(
        self,
        *,
        topic_name: str,
        section_name: str,
        old_section_text: str,
        new_facts: list[dict[str, Any]],
    ) -> str:
        """Call GPT-4o to surgically update a single section with new facts."""
        facts_block = "\n".join(
            f"- {f['fact']}"
            + (f" (Year: {f['year']})" if f.get("year") else "")
            + (" [REPEATED]" if f.get("is_repeated") else "")
            for f in new_facts
        )

        if old_section_text.strip():
            # Update existing section
            system_prompt = _SECTION_UPDATE_SYSTEM_PROMPT.replace(
                "{topic_name}", topic_name,
            )
            user_prompt = (
                f"Section: {section_name}\n\n"
                f"--- EXISTING SECTION TEXT ---\n"
                f"{old_section_text}\n\n"
                f"--- NEW FACT(S) TO INCORPORATE ---\n"
                f"{facts_block}\n\n"
                f"Update the section to incorporate the new fact(s) naturally. "
                f"Do not remove any existing content. Return only the updated section text."
            )
        else:
            # Create new section from scratch
            system_prompt = _NEW_SECTION_SYSTEM_PROMPT.replace(
                "{topic_name}", topic_name,
            ).replace("{section_name}", section_name)
            user_prompt = (
                f"Section heading: {section_name}\n\n"
                f"Facts to incorporate:\n{facts_block}\n\n"
                f"Write a coherent narrative passage for this section."
            )

        logger.info(
            "Updating section '%s' with %d new fact(s) for topic '%s' …",
            section_name, len(new_facts), topic_name,
        )

        updated_text = await self.openai.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            call_type=OpenAICallType.STORY_GENERATION,
            temperature=0.7,
            max_tokens=2048,
        )

        return updated_text.strip()


# ═════════════════════════════════════════════════════════════
# Module-level convenience functions
# ═════════════════════════════════════════════════════════════

async def run_incremental_story_update(
    db: AsyncSession,
    topic_id: UUID,
    paper_id: UUID,
) -> dict[str, Any]:
    """Convenience wrapper — create engine and run paper-based update."""
    engine = IncrementalStoryEngine(db)
    return await engine.update_from_paper(topic_id, paper_id)


async def run_incremental_story_update_from_facts(
    db: AsyncSession,
    topic_id: UUID,
    fact_texts: list[str],
) -> dict[str, Any]:
    """Convenience wrapper — create engine and run fact-list-based update."""
    engine = IncrementalStoryEngine(db)
    return await engine.update_from_facts(topic_id, fact_texts)
