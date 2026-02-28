"""
Embedding Generation & Similarity Check
=========================================
Generates text-embedding-3-small vectors, stores in pgvector,
and checks for near-duplicate questions (cosine similarity > 0.92).
"""

from __future__ import annotations

import logging
import uuid
from uuid import UUID

from sqlalchemy import select, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.services.openai.client import OpenAIService

logger = logging.getLogger(__name__)

_SIMILARITY_THRESHOLD = 0.92  # cosine similarity above this → near-duplicate


def _build_embedding_text(q: dict) -> str:
    """Build a canonical text string from a question dict for embedding."""
    parts = [q.get("question_text", "")]
    for opt_key in ("option_a", "option_b", "option_c", "option_d"):
        opt = q.get(opt_key)
        if opt:
            parts.append(opt)
    return " | ".join(parts)


async def generate_and_store_embeddings(
    db: AsyncSession,
    openai_svc: OpenAIService,
    question_records: list[Question],
    question_dicts: list[dict],
    *,
    batch_size: int = 50,
) -> list[list[float]]:
    """Generate embeddings for all questions and store them in pgvector.

    Parameters
    ----------
    db:
        Async DB session.
    openai_svc:
        OpenAI service for embedding generation.
    question_records:
        ORM Question objects (already persisted with IDs).
    question_dicts:
        The parsed question dicts (parallel to ``question_records``).
    batch_size:
        Embed in batches to respect API limits.

    Returns
    -------
    list[list[float]]
        The embedding vectors (parallel to input lists).
    """
    all_embeddings: list[list[float]] = []

    for i in range(0, len(question_dicts), batch_size):
        batch_dicts = question_dicts[i : i + batch_size]
        batch_records = question_records[i : i + batch_size]
        texts = [_build_embedding_text(q) for q in batch_dicts]

        embeddings = await openai_svc.embed(texts)

        for record, emb in zip(batch_records, embeddings):
            record.embedding = emb  # type: ignore[assignment]
            db.add(record)

        all_embeddings.extend(embeddings)

    await db.flush()
    logger.info("Generated & stored embeddings for %d questions", len(all_embeddings))
    return all_embeddings


async def check_similarity(
    db: AsyncSession,
    question_records: list[Question],
    embeddings: list[list[float]],
    *,
    threshold: float = _SIMILARITY_THRESHOLD,
    exclude_paper_id: UUID | None = None,
) -> dict[str, list]:
    """Compare new question embeddings against all existing questions.

    Flags questions with cosine similarity > threshold as near-duplicates.
    Sets ``is_repeated=True`` and assigns ``similarity_group_id``.

    Parameters
    ----------
    db:
        Async DB session.
    question_records:
        The newly inserted Question ORM objects.
    embeddings:
        Parallel list of embedding vectors.
    threshold:
        Cosine similarity threshold (default 0.92).
    exclude_paper_id:
        Exclude questions from this paper (the current one) during search.

    Returns
    -------
    dict with "duplicates_found" (int) and "details" (list of match info).
    """
    duplicates_found = 0
    details: list[dict] = []

    for record, embedding in zip(question_records, embeddings):
        vec_literal = f"[{','.join(str(v) for v in embedding)}]"

        # Find closest existing question NOT in the same paper
        exclude_clause = ""
        if exclude_paper_id:
            exclude_clause = f"AND paper_id != '{exclude_paper_id}'"

        stmt = sa_text(f"""
            SELECT id, question_number, paper_id, similarity_group_id,
                   1 - (embedding <=> '{vec_literal}'::vector) AS similarity
            FROM questions
            WHERE embedding IS NOT NULL
              AND id != '{record.id}'
              {exclude_clause}
            ORDER BY embedding <=> '{vec_literal}'::vector
            LIMIT 1
        """)

        result = await db.execute(stmt)
        row = result.first()

        if row and float(row.similarity) >= threshold:
            duplicates_found += 1
            existing_id = row.id
            existing_group_id = row.similarity_group_id
            sim_score = float(row.similarity)

            # Assign or reuse similarity_group_id
            if existing_group_id:
                group_id = existing_group_id
            else:
                group_id = uuid.uuid4()
                # Update the existing question's group too
                await db.execute(
                    sa_text(
                        "UPDATE questions SET similarity_group_id = :gid, "
                        "is_repeated = true WHERE id = :qid"
                    ).bindparams(gid=group_id, qid=existing_id)
                )

            record.is_repeated = True
            record.similarity_group_id = group_id
            record.needs_review = True
            record.admin_notes = (
                (record.admin_notes or "")
                + f" | Near-duplicate (similarity={sim_score:.3f}) of question {existing_id}"
            ).strip(" |")
            db.add(record)

            # Update repeat_count for all questions in this group
            await db.execute(
                sa_text(
                    "UPDATE questions SET repeat_count = ("
                    "  SELECT COUNT(*) - 1 FROM questions "
                    "  WHERE similarity_group_id = :gid"
                    ") WHERE similarity_group_id = :gid"
                ).bindparams(gid=group_id)
            )

            details.append({
                "new_question_number": record.question_number,
                "new_question_id": str(record.id),
                "matched_question_id": str(existing_id),
                "similarity": round(sim_score, 4),
                "group_id": str(group_id),
            })

            logger.info(
                "Near-duplicate: Q#%d (%.3f) ← existing %s",
                record.question_number, sim_score, existing_id,
            )

    await db.flush()
    logger.info("Similarity check: %d duplicates found out of %d questions", duplicates_found, len(question_records))

    return {
        "duplicates_found": duplicates_found,
        "details": details,
    }
