"""
Pattern Intelligence Engine
=============================
Runs after every paper ingestion to compute analytics:

1. Topic frequency across all papers per job type
2. Trend direction per topic (rising / falling / stable)
3. Due-topic detection (absent from last 3 papers)
4. Repeat-question tracking (cosine similarity > 0.92)
5. High-frequency facts (appearing in 3+ papers)
6. Pattern snapshot persistence
"""

from __future__ import annotations

import logging
import uuid
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_type import JobType
from app.models.paper import Paper
from app.models.pattern_snapshot import PatternSnapshot
from app.models.question import Question
from app.models.topic import Topic
from app.models.topic_frequency import TopicFrequencyByJob

logger = logging.getLogger(__name__)

# ── Thresholds ───────────────────────────────────────────────
SIMILARITY_THRESHOLD = 0.92
RECENT_PAPER_COUNT = 5       # last N papers for trend analysis
DUE_TOPIC_ABSENCE = 3        # absent from last N papers → "due"
HIGH_FREQ_FACT_MIN = 3       # fact must appear in 3+ papers


class PatternEngine:
    """Stateless service — all state flows through the DB session."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ═════════════════════════════════════════════════════════
    # Public entry point
    # ═════════════════════════════════════════════════════════
    async def run(self, paper_id: UUID, job_type_id: UUID) -> dict[str, Any]:
        """Execute the full pattern-intelligence pipeline for a job type.

        Called after a paper's AI-pipeline completes.
        Returns a summary dict suitable for Celery task results.
        """
        logger.info("Pattern engine START for job_type=%s paper=%s", job_type_id, paper_id)

        # Step 1 — topic frequency
        freq_stats = await self._compute_topic_frequencies(job_type_id)

        # Step 2 — trend directions
        trend_stats = await self._compute_trend_directions(job_type_id)

        # Step 3 — due topics
        due_topics = await self._detect_due_topics(job_type_id)

        # Step 4 — repeat-question tracking
        repeat_stats = await self._track_repeat_questions(job_type_id)

        # Step 5 — high-frequency facts
        high_freq_facts = await self._extract_high_frequency_facts(job_type_id)

        # Step 6 — build & save pattern snapshot
        snapshot_id = await self._save_pattern_snapshot(
            job_type_id=job_type_id,
            freq_stats=freq_stats,
            due_topics=due_topics,
            high_freq_facts=high_freq_facts,
        )

        # Flush everything
        await self.db.flush()

        summary = {
            "status": "completed",
            "job_type_id": str(job_type_id),
            "paper_id": str(paper_id),
            "snapshot_id": str(snapshot_id),
            "topics_computed": freq_stats["topics_computed"],
            "trends_updated": trend_stats["updated"],
            "due_topics_flagged": len(due_topics),
            "repeat_groups_found": repeat_stats["groups"],
            "high_freq_facts_count": len(high_freq_facts),
        }
        logger.info("Pattern engine DONE: %s", summary)
        return summary

    # ═════════════════════════════════════════════════════════
    # 1. Topic frequency
    # ═════════════════════════════════════════════════════════
    async def _compute_topic_frequencies(self, job_type_id: UUID) -> dict[str, Any]:
        """Count questions-per-topic-per-paper, store in topic_frequency_by_job."""

        # All papers for this job type ordered by year
        papers_q = (
            select(Paper)
            .where(Paper.job_type_id == job_type_id, Paper.ingestion_status == "completed")
            .order_by(Paper.paper_year.asc())
        )
        papers_result = await self.db.execute(papers_q)
        papers = papers_result.scalars().all()

        topics_computed = 0

        for paper in papers:
            # Count questions per topic in this paper
            count_q = (
                select(Question.topic_id, func.count(Question.id).label("cnt"))
                .where(Question.paper_id == paper.id, Question.topic_id.isnot(None))
                .group_by(Question.topic_id)
            )
            rows = (await self.db.execute(count_q)).all()

            total_qs = sum(r.cnt for r in rows) or 1  # avoid div-by-zero

            for row in rows:
                pct = round((row.cnt / total_qs) * 100, 2)

                # Upsert into topic_frequency_by_job
                existing_q = select(TopicFrequencyByJob).where(
                    TopicFrequencyByJob.topic_id == row.topic_id,
                    TopicFrequencyByJob.job_type_id == job_type_id,
                    TopicFrequencyByJob.year == paper.paper_year,
                )
                existing = (await self.db.execute(existing_q)).scalar_one_or_none()

                if existing:
                    existing.question_count = row.cnt
                    existing.percentage_of_paper = pct
                else:
                    self.db.add(TopicFrequencyByJob(
                        topic_id=row.topic_id,
                        job_type_id=job_type_id,
                        year=paper.paper_year,
                        question_count=row.cnt,
                        percentage_of_paper=pct,
                    ))
                topics_computed += 1

        await self.db.flush()
        return {"topics_computed": topics_computed}

    # ═════════════════════════════════════════════════════════
    # 2. Trend direction per topic
    # ═════════════════════════════════════════════════════════
    async def _compute_trend_directions(self, job_type_id: UUID) -> dict[str, int]:
        """Compare avg frequency in last 5 papers vs older papers.

        Sets topic.trend_direction to 'rising', 'falling', or 'stable'.
        """
        # Get distinct paper years for this job type (descending)
        years_q = (
            select(Paper.paper_year)
            .where(Paper.job_type_id == job_type_id, Paper.ingestion_status == "completed")
            .distinct()
            .order_by(Paper.paper_year.desc())
        )
        years = [r for (r,) in (await self.db.execute(years_q)).all()]

        if len(years) < 2:
            # Not enough data for trend comparison
            return {"updated": 0}

        recent_years = set(years[:RECENT_PAPER_COUNT])
        older_years = set(years[RECENT_PAPER_COUNT:]) if len(years) > RECENT_PAPER_COUNT else set()

        if not older_years:
            # All data is "recent", mark as stable
            await self.db.execute(
                update(Topic).values(trend_direction="stable")
            )
            await self.db.flush()
            count_q = select(func.count(Topic.id))
            total = (await self.db.execute(count_q)).scalar() or 0
            return {"updated": total}

        # Fetch all frequency rows for this job type
        freq_q = (
            select(TopicFrequencyByJob)
            .where(TopicFrequencyByJob.job_type_id == job_type_id)
        )
        freq_rows = (await self.db.execute(freq_q)).scalars().all()

        # Build per-topic recent vs older averages
        recent_counts: dict[UUID, list[int]] = defaultdict(list)
        older_counts: dict[UUID, list[int]] = defaultdict(list)

        for fr in freq_rows:
            if fr.year in recent_years:
                recent_counts[fr.topic_id].append(fr.question_count)
            elif fr.year in older_years:
                older_counts[fr.topic_id].append(fr.question_count)

        updated = 0
        all_topic_ids = set(recent_counts.keys()) | set(older_counts.keys())

        for topic_id in all_topic_ids:
            recent_avg = (
                sum(recent_counts[topic_id]) / len(recent_counts[topic_id])
                if recent_counts[topic_id] else 0
            )
            older_avg = (
                sum(older_counts[topic_id]) / len(older_counts[topic_id])
                if older_counts[topic_id] else 0
            )

            if older_avg == 0:
                direction = "rising" if recent_avg > 0 else "stable"
            else:
                change_ratio = (recent_avg - older_avg) / older_avg
                if change_ratio > 0.15:
                    direction = "rising"
                elif change_ratio < -0.15:
                    direction = "falling"
                else:
                    direction = "stable"

            await self.db.execute(
                update(Topic)
                .where(Topic.id == topic_id)
                .values(trend_direction=direction)
            )
            updated += 1

        await self.db.flush()
        return {"updated": updated}

    # ═════════════════════════════════════════════════════════
    # 3. Due-topic detection
    # ═════════════════════════════════════════════════════════
    async def _detect_due_topics(self, job_type_id: UUID) -> list[dict[str, Any]]:
        """Topics absent from the last N papers of a job type → flagged 'due'."""

        # Get the last N papers for this job type
        recent_papers_q = (
            select(Paper.id)
            .where(Paper.job_type_id == job_type_id, Paper.ingestion_status == "completed")
            .order_by(Paper.paper_year.desc())
            .limit(DUE_TOPIC_ABSENCE)
        )
        recent_paper_ids = [
            r for (r,) in (await self.db.execute(recent_papers_q)).all()
        ]

        if not recent_paper_ids:
            return []

        # Topics that DO appear in these papers
        present_topics_q = (
            select(Question.topic_id)
            .where(
                Question.paper_id.in_(recent_paper_ids),
                Question.topic_id.isnot(None),
            )
            .distinct()
        )
        present_topic_ids = set(
            r for (r,) in (await self.db.execute(present_topics_q)).all()
        )

        # Topics that have historically appeared for this job type but are now absent
        all_topics_q = (
            select(TopicFrequencyByJob.topic_id)
            .where(TopicFrequencyByJob.job_type_id == job_type_id)
            .distinct()
        )
        all_topic_ids = set(
            r for (r,) in (await self.db.execute(all_topics_q)).all()
        )

        due_topic_ids = all_topic_ids - present_topic_ids

        due_topics: list[dict[str, Any]] = []
        for tid in due_topic_ids:
            topic = await self.db.get(Topic, tid)
            if topic:
                due_topics.append({
                    "topic_id": str(tid),
                    "topic_name": topic.name,
                    "display_name": topic.display_name,
                    "absent_papers": DUE_TOPIC_ABSENCE,
                })

        return due_topics

    # ═════════════════════════════════════════════════════════
    # 4. Repeat-question tracking (cosine similarity)
    # ═════════════════════════════════════════════════════════
    async def _track_repeat_questions(self, job_type_id: UUID) -> dict[str, int]:
        """Use pgvector cosine distance to find repeated questions across papers.

        For every question with an embedding in this job type's papers,
        find others within SIMILARITY_THRESHOLD and update is_repeated /
        repeat_count / similarity_group_id.
        """
        # Get all paper IDs for this job type
        paper_ids_q = (
            select(Paper.id)
            .where(Paper.job_type_id == job_type_id, Paper.ingestion_status == "completed")
        )
        paper_ids = [r for (r,) in (await self.db.execute(paper_ids_q)).all()]

        if not paper_ids:
            return {"groups": 0}

        # Get all questions with embeddings in these papers
        questions_q = (
            select(Question.id, Question.paper_id, Question.embedding, Question.similarity_group_id)
            .where(
                Question.paper_id.in_(paper_ids),
                Question.embedding.isnot(None),
            )
        )
        questions = (await self.db.execute(questions_q)).all()

        if len(questions) < 2:
            return {"groups": 0}

        # Use pgvector <=> (cosine distance) to find pairs.
        # cosine_distance = 1 - cosine_similarity
        # similarity > 0.92  →  distance < 0.08
        max_distance = 1.0 - SIMILARITY_THRESHOLD
        groups_created = 0

        for q in questions:
            if q.similarity_group_id:
                # Already assigned to a group — skip discovery but update count
                continue

            # Find similar questions (excluding self, across different papers)
            similar_q = text("""
                SELECT id
                FROM questions
                WHERE id != :qid
                  AND paper_id = ANY(:paper_ids)
                  AND embedding IS NOT NULL
                  AND (embedding <=> :embedding) < :max_dist
            """)
            result = await self.db.execute(
                similar_q,
                {
                    "qid": q.id,
                    "paper_ids": paper_ids,
                    "embedding": str(q.embedding),
                    "max_dist": max_distance,
                },
            )
            similar_ids = [r[0] for r in result.all()]

            if similar_ids:
                # Create or reuse a group ID
                group_id = q.similarity_group_id or uuid.uuid4()
                all_ids = [q.id] + similar_ids
                repeat_count = len(all_ids)

                await self.db.execute(
                    update(Question)
                    .where(Question.id.in_(all_ids))
                    .values(
                        is_repeated=True,
                        repeat_count=repeat_count,
                        similarity_group_id=group_id,
                    )
                )
                groups_created += 1

        await self.db.flush()
        return {"groups": groups_created}

    # ═════════════════════════════════════════════════════════
    # 5. High-frequency facts
    # ═════════════════════════════════════════════════════════
    async def _extract_high_frequency_facts(
        self, job_type_id: UUID
    ) -> list[dict[str, Any]]:
        """Facts appearing in 3+ distinct papers → high-frequency.

        Uses exact-match grouping on fact_extracted; for fuzzy matching
        a future iteration can use embeddings.
        """
        paper_ids_q = (
            select(Paper.id)
            .where(Paper.job_type_id == job_type_id, Paper.ingestion_status == "completed")
        )
        paper_ids = [r for (r,) in (await self.db.execute(paper_ids_q)).all()]

        if not paper_ids:
            return []

        # Count distinct papers each fact appears in
        fact_q = (
            select(
                Question.fact_extracted,
                func.count(func.distinct(Question.paper_id)).label("paper_count"),
                func.count(Question.id).label("total_appearances"),
            )
            .where(
                Question.paper_id.in_(paper_ids),
                Question.fact_extracted.isnot(None),
                Question.fact_extracted != "",
            )
            .group_by(Question.fact_extracted)
            .having(func.count(func.distinct(Question.paper_id)) >= HIGH_FREQ_FACT_MIN)
            .order_by(func.count(func.distinct(Question.paper_id)).desc())
        )
        rows = (await self.db.execute(fact_q)).all()

        return [
            {
                "fact": row.fact_extracted,
                "paper_count": row.paper_count,
                "total_appearances": row.total_appearances,
            }
            for row in rows
        ]

    # ═════════════════════════════════════════════════════════
    # 6. Pattern snapshot
    # ═════════════════════════════════════════════════════════
    async def _save_pattern_snapshot(
        self,
        job_type_id: UUID,
        freq_stats: dict[str, Any],
        due_topics: list[dict[str, Any]],
        high_freq_facts: list[dict[str, Any]],
    ) -> UUID:
        """Persist a pattern_snapshots record with current analytics."""

        # Paper count for this job type
        paper_count_q = (
            select(func.count(Paper.id))
            .where(Paper.job_type_id == job_type_id, Paper.ingestion_status == "completed")
        )
        paper_count = (await self.db.execute(paper_count_q)).scalar() or 0

        # Build predicted topic ratios from latest frequency data
        latest_year_q = (
            select(func.max(TopicFrequencyByJob.year))
            .where(TopicFrequencyByJob.job_type_id == job_type_id)
        )
        latest_year = (await self.db.execute(latest_year_q)).scalar()

        topic_ratios: dict[str, Any] = {}
        if latest_year:
            freq_q = (
                select(TopicFrequencyByJob, Topic.name.label("topic_name"))
                .join(Topic, TopicFrequencyByJob.topic_id == Topic.id)
                .where(
                    TopicFrequencyByJob.job_type_id == job_type_id,
                    TopicFrequencyByJob.year == latest_year,
                )
                .order_by(TopicFrequencyByJob.percentage_of_paper.desc())
            )
            freq_rows = (await self.db.execute(freq_q)).all()

            for row in freq_rows:
                tf = row[0]  # TopicFrequencyByJob object
                topic_name = row.topic_name
                topic_ratios[topic_name] = {
                    "percentage": tf.percentage_of_paper,
                    "question_count": tf.question_count,
                    "trend": None,  # will be populated from topic model
                }

            # Enrich with trend directions
            for topic_name in topic_ratios:
                topic_q = select(Topic).where(Topic.name == topic_name)
                topic = (await self.db.execute(topic_q)).scalar_one_or_none()
                if topic:
                    topic_ratios[topic_name]["trend"] = topic.trend_direction

        # Confidence score: simple heuristic based on paper count
        # More papers → higher confidence, capped at 0.95
        confidence = min(0.95, 0.3 + (paper_count * 0.05))

        # Build high-probability facts payload
        facts_payload = {
            "facts": high_freq_facts,
            "due_topics": due_topics,
        }

        snapshot = PatternSnapshot(
            job_type_id=job_type_id,
            snapshot_date=date.today(),
            paper_count_at_snapshot=paper_count,
            predicted_topic_ratios=topic_ratios,
            confidence_score=round(confidence, 3),
            high_probability_facts=facts_payload,
        )
        self.db.add(snapshot)
        await self.db.flush()

        # Also update the JobType.topic_ratios for quick access
        await self.db.execute(
            update(JobType)
            .where(JobType.id == job_type_id)
            .values(
                topic_ratios=topic_ratios,
                last_updated_ratios=datetime.now(timezone.utc),
            )
        )

        return snapshot.id


# ── Convenience wrapper ──────────────────────────────────────
async def run_pattern_engine(
    db: AsyncSession,
    paper_id: UUID,
    job_type_id: UUID,
) -> dict[str, Any]:
    """Functional entry-point for callers that prefer not to instantiate the class."""
    engine = PatternEngine(db)
    return await engine.run(paper_id, job_type_id)
