"""
Prediction Engine
===================
AI-powered exam prediction pipeline that generates full predicted papers.

Algorithm:
1. Load job type's learned topic_ratios from latest pattern_snapshot.
2. For each topic slot, apply weighted probability:
   - Topic Recency 30% (topics in last 2 papers get lower weight)
   - Topic Frequency 25%
   - Due Topics 20% (absent 3+ papers get boost)
   - Subtopic Variation 15%
   - Question Type Pattern 10%
3. Retrieve top representative questions per topic via pgvector similarity.
4. Generate fresh MCQs using GPT-4o (novel questions testing same facts).
5. Optionally add current affairs MCQs from recent items.
6. Calculate confidence_score based on paper count, pattern consistency, recency.
7. Persist prediction record.
"""

from __future__ import annotations

import json
import logging
import math
import uuid
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, AsyncGenerator
from uuid import UUID

from sqlalchemy import func, select, text, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.current_affair import CurrentAffairsItem
from app.models.job_type import JobType
from app.models.paper import Paper
from app.models.pattern_snapshot import PatternSnapshot
from app.models.prediction import Prediction
from app.models.question import Question
from app.models.topic import Topic
from app.models.topic_frequency import TopicFrequencyByJob
from app.services.openai.client import OpenAIService, get_openai_service
from app.services.openai.models import OpenAICallType

logger = logging.getLogger(__name__)

# ── Weight constants ─────────────────────────────────────────
WEIGHT_RECENCY = 0.30
WEIGHT_FREQUENCY = 0.25
WEIGHT_DUE_TOPICS = 0.20
WEIGHT_SUBTOPIC_VARIATION = 0.15
WEIGHT_QUESTION_TYPE = 0.10

# ── Thresholds ───────────────────────────────────────────────
DUE_TOPIC_ABSENCE_THRESHOLD = 3
CURRENT_AFFAIRS_DAYS_MIN = 60
CURRENT_AFFAIRS_DAYS_MAX = 90
CURRENT_AFFAIRS_RATIO = 0.15  # up to 15% of total questions from current affairs
REPRESENTATIVE_QUESTIONS_PER_TOPIC = 5
SIMILARITY_SEARCH_LIMIT = 10


class PredictionEngine:
    """Stateless prediction service — all state flows through the DB session."""

    def __init__(self, db: AsyncSession, openai: OpenAIService | None = None) -> None:
        self.db = db
        self.openai = openai or get_openai_service()

    # ═════════════════════════════════════════════════════════
    # Public: streaming generator
    # ═════════════════════════════════════════════════════════
    async def generate_streaming(
        self,
        job_type_id: UUID,
        prediction_date: date,
        include_current_affairs: bool = True,
        total_questions: int = 100,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Yield SSE events as questions are generated one by one.

        Event types:
        - status: progress updates
        - question: individual MCQ generated
        - current_affair: current affairs MCQ
        - confidence: confidence scoring result
        - complete: final summary
        - error: on failure
        """
        prediction_id: UUID | None = None
        try:
            # ── Step 0: Validate job type ────────────────────
            job_type = await self.db.get(JobType, job_type_id)
            if not job_type:
                yield {"event": "error", "data": {"message": f"Job type {job_type_id} not found"}}
                return

            # Create the prediction record upfront
            title = f"Predicted Paper — {job_type.name} — {prediction_date.strftime('%B %Y')}"
            prediction = Prediction(
                job_type_id=job_type_id,
                title=title,
                prediction_date=prediction_date,
                total_questions=total_questions,
                include_current_affairs=include_current_affairs,
                status="generating",
            )
            self.db.add(prediction)
            await self.db.flush()
            await self.db.refresh(prediction)
            prediction_id = prediction.id

            yield {
                "event": "status",
                "data": {
                    "prediction_id": str(prediction_id),
                    "message": f"Starting prediction for {job_type.name}",
                    "step": "init",
                    "progress": 0,
                },
            }

            # ── Step 1: Load topic ratios from latest snapshot ─
            yield {
                "event": "status",
                "data": {"message": "Loading topic patterns…", "step": "load_patterns", "progress": 5},
            }
            snapshot, topic_ratios = await self._load_topic_ratios(job_type_id)

            if not topic_ratios:
                yield {
                    "event": "status",
                    "data": {"message": "No pattern data found — using uniform distribution", "step": "fallback"},
                }
                topic_ratios = await self._fallback_uniform_distribution(job_type_id)

            if snapshot:
                prediction.snapshot_id = snapshot.id

            # ── Step 2: Compute weighted topic allocation ────
            yield {
                "event": "status",
                "data": {"message": "Computing topic allocation weights…", "step": "weights", "progress": 10},
            }

            ca_question_count = 0
            main_question_count = total_questions
            if include_current_affairs:
                ca_question_count = min(
                    int(total_questions * CURRENT_AFFAIRS_RATIO),
                    max(5, int(total_questions * 0.10)),
                )
                main_question_count = total_questions - ca_question_count

            topic_allocation = await self._compute_weighted_allocation(
                job_type_id=job_type_id,
                topic_ratios=topic_ratios,
                total_slots=main_question_count,
            )

            prediction.topic_distribution = {
                name: count for name, count in topic_allocation.items()
            }

            yield {
                "event": "status",
                "data": {
                    "message": f"Allocated {main_question_count} questions across {len(topic_allocation)} topics",
                    "step": "allocation_done",
                    "progress": 15,
                    "topic_allocation": {k: v for k, v in topic_allocation.items()},
                },
            }

            # ── Step 3–4: Generate MCQs per topic ───────────
            all_questions: list[dict[str, Any]] = []
            question_number = 0
            total_topics = len(topic_allocation)

            for idx, (topic_name, slot_count) in enumerate(topic_allocation.items()):
                if slot_count <= 0:
                    continue

                progress = 15 + int((idx / max(total_topics, 1)) * 65)
                yield {
                    "event": "status",
                    "data": {
                        "message": f"Generating {slot_count} questions for '{topic_name}'…",
                        "step": "generating",
                        "progress": progress,
                        "topic": topic_name,
                    },
                }

                # Step 3: Retrieve representative questions via pgvector
                representative_qs = await self._get_representative_questions(
                    job_type_id=job_type_id,
                    topic_name=topic_name,
                    limit=REPRESENTATIVE_QUESTIONS_PER_TOPIC,
                )

                # Step 4: Generate fresh MCQs with GPT-4o
                generated = await self._generate_mcqs_for_topic(
                    topic_name=topic_name,
                    slot_count=slot_count,
                    representative_questions=representative_qs,
                    job_type_name=job_type.name,
                    prediction_date=prediction_date,
                )

                for q in generated:
                    question_number += 1
                    q["question_number"] = question_number
                    all_questions.append(q)

                    # Stream each question as it's generated
                    yield {
                        "event": "question",
                        "data": q,
                    }

            prediction.questions_json = {"questions": all_questions}

            # ── Step 5: Current affairs ──────────────────────
            ca_questions: list[dict[str, Any]] = []
            if include_current_affairs and ca_question_count > 0:
                yield {
                    "event": "status",
                    "data": {
                        "message": f"Generating {ca_question_count} current affairs questions…",
                        "step": "current_affairs",
                        "progress": 82,
                    },
                }

                ca_questions = await self._generate_current_affairs_mcqs(
                    ca_question_count=ca_question_count,
                    prediction_date=prediction_date,
                    start_number=question_number + 1,
                )

                for caq in ca_questions:
                    yield {"event": "current_affair", "data": caq}

                prediction.current_affairs_json = {"questions": ca_questions}

            # ── Step 6: Calculate confidence score ───────────
            yield {
                "event": "status",
                "data": {"message": "Calculating confidence score…", "step": "confidence", "progress": 90},
            }

            confidence_data = await self._calculate_confidence(
                job_type_id=job_type_id,
                snapshot=snapshot,
            )
            prediction.confidence_score = confidence_data["confidence_score"]
            prediction.paper_count_basis = confidence_data["paper_count"]
            prediction.pattern_consistency = confidence_data["pattern_consistency"]

            yield {
                "event": "confidence",
                "data": confidence_data,
            }

            # ── Step 7: Finalize ─────────────────────────────
            prediction.status = "completed"
            prediction.generation_metadata = {
                "algorithm_version": "1.0",
                "weights": {
                    "recency": WEIGHT_RECENCY,
                    "frequency": WEIGHT_FREQUENCY,
                    "due_topics": WEIGHT_DUE_TOPICS,
                    "subtopic_variation": WEIGHT_SUBTOPIC_VARIATION,
                    "question_type": WEIGHT_QUESTION_TYPE,
                },
                "representative_qs_per_topic": REPRESENTATIVE_QUESTIONS_PER_TOPIC,
                "current_affairs_days_range": [CURRENT_AFFAIRS_DAYS_MIN, CURRENT_AFFAIRS_DAYS_MAX],
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            self.db.add(prediction)
            await self.db.flush()

            yield {
                "event": "complete",
                "data": {
                    "prediction_id": str(prediction_id),
                    "status": "completed",
                    "total_questions_generated": len(all_questions),
                    "current_affairs_count": len(ca_questions),
                    "confidence_score": confidence_data["confidence_score"],
                    "message": "Prediction generation complete",
                },
            }

        except Exception as exc:
            logger.exception("Prediction engine failed: %s", exc)
            if prediction_id:
                try:
                    pred = await self.db.get(Prediction, prediction_id)
                    if pred:
                        pred.status = "failed"
                        pred.generation_metadata = {
                            "error": str(exc),
                            "failed_at": datetime.now(timezone.utc).isoformat(),
                        }
                        self.db.add(pred)
                        await self.db.flush()
                except Exception:
                    logger.exception("Failed to update prediction status on error")
            yield {
                "event": "error",
                "data": {"message": f"Prediction generation failed: {exc}"},
            }

    # ═════════════════════════════════════════════════════════
    # Step 1: Load topic ratios
    # ═════════════════════════════════════════════════════════
    async def _load_topic_ratios(
        self, job_type_id: UUID
    ) -> tuple[PatternSnapshot | None, dict[str, Any]]:
        """Load the latest pattern snapshot's predicted_topic_ratios."""
        snapshot_q = (
            select(PatternSnapshot)
            .where(PatternSnapshot.job_type_id == job_type_id)
            .order_by(PatternSnapshot.snapshot_date.desc())
            .limit(1)
        )
        snapshot = (await self.db.execute(snapshot_q)).scalar_one_or_none()

        if not snapshot or not snapshot.predicted_topic_ratios:
            # Fallback: check JobType.topic_ratios
            jt = await self.db.get(JobType, job_type_id)
            if jt and jt.topic_ratios:
                return None, jt.topic_ratios
            return None, {}

        return snapshot, snapshot.predicted_topic_ratios

    async def _fallback_uniform_distribution(
        self, job_type_id: UUID
    ) -> dict[str, Any]:
        """If no pattern data exists, build uniform distribution from all known topics."""
        topics_q = (
            select(Topic.name, func.count(Question.id).label("q_count"))
            .outerjoin(Question, Question.topic_id == Topic.id)
            .group_by(Topic.name)
            .having(func.count(Question.id) > 0)
            .order_by(func.count(Question.id).desc())
            .limit(30)
        )
        rows = (await self.db.execute(topics_q)).all()
        if not rows:
            return {}

        total_qs = sum(r.q_count for r in rows)
        return {
            r.name: {
                "percentage": round((r.q_count / total_qs) * 100, 2),
                "question_count": r.q_count,
                "trend": None,
            }
            for r in rows
        }

    # ═════════════════════════════════════════════════════════
    # Step 2: Weighted topic allocation
    # ═════════════════════════════════════════════════════════
    async def _compute_weighted_allocation(
        self,
        job_type_id: UUID,
        topic_ratios: dict[str, Any],
        total_slots: int,
    ) -> dict[str, int]:
        """Compute how many questions each topic gets, using 5-factor weighting."""

        # Get the last 2 papers for recency weighting
        recent_papers_q = (
            select(Paper.id)
            .where(Paper.job_type_id == job_type_id, Paper.ingestion_status == "completed")
            .order_by(Paper.paper_year.desc())
            .limit(2)
        )
        recent_paper_ids = [
            r for (r,) in (await self.db.execute(recent_papers_q)).all()
        ]

        # Topics present in last 2 papers
        recent_topic_names: set[str] = set()
        if recent_paper_ids:
            recent_topics_q = (
                select(Topic.name)
                .join(Question, Question.topic_id == Topic.id)
                .where(Question.paper_id.in_(recent_paper_ids))
                .distinct()
            )
            recent_topic_names = {
                r for (r,) in (await self.db.execute(recent_topics_q)).all()
            }

        # Due topics (absent from last 3+ papers)
        due_topic_names = await self._get_due_topic_names(job_type_id)

        # Subtopic diversity map: topic_name → number of distinct subtopics
        subtopic_q = (
            select(Topic.name, func.count(func.distinct(Question.subtopic)).label("sub_count"))
            .join(Question, Question.topic_id == Topic.id)
            .join(Paper, Question.paper_id == Paper.id)
            .where(Paper.job_type_id == job_type_id, Question.subtopic.isnot(None))
            .group_by(Topic.name)
        )
        subtopic_diversity = {
            r.name: r.sub_count
            for r in (await self.db.execute(subtopic_q)).all()
        }
        max_subtopics = max(subtopic_diversity.values()) if subtopic_diversity else 1

        # Question type distribution: topic_name → variety of question patterns
        # We approximate by counting distinct difficulty score ranges
        qtype_q = (
            select(
                Topic.name,
                func.count(func.distinct(
                    func.round(Question.difficulty_score * 10)  # bucket by 0.1 steps
                )).label("type_variety")
            )
            .join(Question, Question.topic_id == Topic.id)
            .join(Paper, Question.paper_id == Paper.id)
            .where(Paper.job_type_id == job_type_id)
            .group_by(Topic.name)
        )
        qtype_variety = {
            r.name: r.type_variety
            for r in (await self.db.execute(qtype_q)).all()
        }
        max_variety = max(qtype_variety.values()) if qtype_variety else 1

        # Compute weighted score per topic
        scored: dict[str, float] = {}
        for topic_name, info in topic_ratios.items():
            base_pct = float(info.get("percentage", 0)) if isinstance(info, dict) else 0

            # Factor 1: Topic Recency (30%) — topics in last 2 papers get LOWER weight
            # to promote diversity (they were recently tested)
            recency_score = 0.3 if topic_name in recent_topic_names else 1.0

            # Factor 2: Topic Frequency (25%) — directly from historical percentage
            frequency_score = base_pct / 100.0 if base_pct > 0 else 0.01

            # Factor 3: Due Topics (20%) — absent 3+ papers get boost
            due_score = 1.5 if topic_name in due_topic_names else 0.5

            # Factor 4: Subtopic Variation (15%) — more subtopics = richer topic
            sub_count = subtopic_diversity.get(topic_name, 1)
            subtopic_score = sub_count / max_subtopics

            # Factor 5: Question Type Pattern (10%) — more variety = higher weight
            variety = qtype_variety.get(topic_name, 1)
            qtype_score = variety / max_variety

            # Weighted sum
            total_score = (
                WEIGHT_RECENCY * recency_score
                + WEIGHT_FREQUENCY * frequency_score
                + WEIGHT_DUE_TOPICS * due_score
                + WEIGHT_SUBTOPIC_VARIATION * subtopic_score
                + WEIGHT_QUESTION_TYPE * qtype_score
            )
            scored[topic_name] = total_score

        # Normalize and allocate slots
        total_weight = sum(scored.values()) or 1.0
        allocation: dict[str, int] = {}
        allocated = 0

        for topic_name, weight in sorted(scored.items(), key=lambda x: -x[1]):
            count = max(1, round((weight / total_weight) * total_slots))
            if allocated + count > total_slots:
                count = total_slots - allocated
            if count <= 0:
                continue
            allocation[topic_name] = count
            allocated += count
            if allocated >= total_slots:
                break

        # Distribute remaining slots to top topics
        remaining = total_slots - allocated
        if remaining > 0:
            sorted_topics = sorted(scored.items(), key=lambda x: -x[1])
            for i, (tn, _) in enumerate(sorted_topics):
                if remaining <= 0:
                    break
                if tn in allocation:
                    allocation[tn] += 1
                    remaining -= 1

        return allocation

    async def _get_due_topic_names(self, job_type_id: UUID) -> set[str]:
        """Topics absent from the last N papers → flagged as 'due'."""
        recent_papers_q = (
            select(Paper.id)
            .where(Paper.job_type_id == job_type_id, Paper.ingestion_status == "completed")
            .order_by(Paper.paper_year.desc())
            .limit(DUE_TOPIC_ABSENCE_THRESHOLD)
        )
        recent_paper_ids = [
            r for (r,) in (await self.db.execute(recent_papers_q)).all()
        ]
        if not recent_paper_ids:
            return set()

        # Topics present in recent papers
        present_q = (
            select(Topic.name)
            .join(Question, Question.topic_id == Topic.id)
            .where(Question.paper_id.in_(recent_paper_ids))
            .distinct()
        )
        present_names = {r for (r,) in (await self.db.execute(present_q)).all()}

        # All topics that have historically appeared for this job type
        all_topics_q = (
            select(Topic.name)
            .join(TopicFrequencyByJob, TopicFrequencyByJob.topic_id == Topic.id)
            .where(TopicFrequencyByJob.job_type_id == job_type_id)
            .distinct()
        )
        all_names = {r for (r,) in (await self.db.execute(all_topics_q)).all()}

        return all_names - present_names

    # ═════════════════════════════════════════════════════════
    # Step 3: Representative questions via pgvector
    # ═════════════════════════════════════════════════════════
    async def _get_representative_questions(
        self,
        job_type_id: UUID,
        topic_name: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve top representative questions for a topic using pgvector similarity.

        Picks high-frequency, well-embedded questions that best represent
        what this topic tests in past papers.
        """
        # Get topic ID
        topic = (
            await self.db.execute(select(Topic).where(Topic.name == topic_name))
        ).scalar_one_or_none()

        if not topic:
            return []

        # Get paper IDs for this job type
        paper_ids_q = (
            select(Paper.id)
            .where(Paper.job_type_id == job_type_id, Paper.ingestion_status == "completed")
        )
        paper_ids = [r for (r,) in (await self.db.execute(paper_ids_q)).all()]
        if not paper_ids:
            return []

        # Get questions with embeddings for this topic, ordered by repeat_count
        # (most representative = most repeated / highest frequency)
        questions_q = (
            select(Question)
            .where(
                Question.topic_id == topic.id,
                Question.paper_id.in_(paper_ids),
                Question.embedding.isnot(None),
            )
            .order_by(
                Question.repeat_count.desc(),
                Question.difficulty_score.asc(),
            )
            .limit(limit)
        )
        questions = (await self.db.execute(questions_q)).scalars().all()

        # If not enough with embeddings, fall back to any questions for this topic
        if len(questions) < limit:
            fallback_q = (
                select(Question)
                .where(
                    Question.topic_id == topic.id,
                    Question.paper_id.in_(paper_ids),
                )
                .order_by(Question.repeat_count.desc())
                .limit(limit)
            )
            questions = (await self.db.execute(fallback_q)).scalars().all()

        return [
            {
                "question_text": q.question_text,
                "option_a": q.option_a,
                "option_b": q.option_b,
                "option_c": q.option_c,
                "option_d": q.option_d,
                "correct_answer": q.correct_answer,
                "fact_extracted": q.fact_extracted,
                "subtopic": q.subtopic,
                "difficulty_score": q.difficulty_score,
                "repeat_count": q.repeat_count,
                "year_appeared": q.year_appeared,
            }
            for q in questions
        ]

    # ═════════════════════════════════════════════════════════
    # Step 4: Generate fresh MCQs with GPT-4o
    # ═════════════════════════════════════════════════════════
    async def _generate_mcqs_for_topic(
        self,
        topic_name: str,
        slot_count: int,
        representative_questions: list[dict[str, Any]],
        job_type_name: str,
        prediction_date: date,
    ) -> list[dict[str, Any]]:
        """Use GPT-4o to generate novel MCQs testing the same high-frequency facts."""

        # Build context from representative questions
        examples_text = ""
        facts_list = []
        for i, q in enumerate(representative_questions, 1):
            examples_text += f"\n--- Example {i} ---\n"
            examples_text += f"Q: {q['question_text']}\n"
            if q.get("option_a"):
                examples_text += f"A) {q['option_a']}\nB) {q['option_b']}\nC) {q['option_c']}\nD) {q['option_d']}\n"
            if q.get("correct_answer"):
                examples_text += f"Correct: {q['correct_answer']}\n"
            if q.get("fact_extracted"):
                examples_text += f"Key Fact: {q['fact_extracted']}\n"
                facts_list.append(q["fact_extracted"])
            if q.get("subtopic"):
                examples_text += f"Subtopic: {q['subtopic']}\n"

        system_prompt = f"""You are an expert PPSC exam question designer for Pakistan's provincial public service examinations.

Your task: Generate {slot_count} FRESH, NOVEL multiple-choice questions for the topic "{topic_name}" 
targeting the {job_type_name} exam predicted for {prediction_date.strftime('%B %Y')}.

CRITICAL RULES:
1. Questions must test the SAME high-frequency facts and concepts from past papers but with DIFFERENT wording and angles.
2. Each question must have exactly 4 options (A, B, C, D) with exactly 1 correct answer.
3. Questions must be factually accurate and at PPSC difficulty level.
4. Do NOT copy questions verbatim — rephrase and create new question stems.
5. Include a mix of difficulty levels.
6. For each question, identify the specific fact being tested.

Return ONLY valid JSON array with this structure:
[
  {{
    "question_text": "...",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_answer": "a",
    "subtopic": "...",
    "difficulty_score": 0.5,
    "fact_basis": "The specific fact this question tests",
    "confidence": 0.8
  }}
]"""

        user_prompt = f"""Generate {slot_count} questions for topic "{topic_name}".

Here are representative past paper questions to understand the patterns and facts tested:
{examples_text}

Key facts that frequently appear:
{chr(10).join(f'- {f}' for f in facts_list) if facts_list else '(No extracted facts available — use your knowledge of PPSC patterns)'}

Generate {slot_count} NEW questions that test these same concepts from fresh angles."""

        try:
            response = await self.openai.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                call_type=OpenAICallType.PREDICTION_GENERATION,
                temperature=0.6,
                response_format={"type": "json_object"},
            )

            # Parse JSON response
            parsed = json.loads(response)
            questions_raw = parsed if isinstance(parsed, list) else parsed.get("questions", [])

            # Normalize and validate
            result: list[dict[str, Any]] = []
            for q in questions_raw[:slot_count]:
                result.append({
                    "question_text": q.get("question_text", ""),
                    "option_a": q.get("option_a", ""),
                    "option_b": q.get("option_b", ""),
                    "option_c": q.get("option_c", ""),
                    "option_d": q.get("option_d", ""),
                    "correct_answer": q.get("correct_answer", "a"),
                    "topic_name": topic_name,
                    "subtopic": q.get("subtopic"),
                    "difficulty_score": q.get("difficulty_score", 0.5),
                    "fact_basis": q.get("fact_basis"),
                    "is_current_affairs": False,
                    "confidence": q.get("confidence", 0.7),
                })
            return result

        except Exception as exc:
            logger.exception("GPT-4o MCQ generation failed for topic '%s': %s", topic_name, exc)
            # Return placeholder on failure
            return [
                {
                    "question_text": f"[Generation failed for {topic_name} - Q{i+1}]",
                    "option_a": "—",
                    "option_b": "—",
                    "option_c": "—",
                    "option_d": "—",
                    "correct_answer": "a",
                    "topic_name": topic_name,
                    "subtopic": None,
                    "difficulty_score": 0.5,
                    "fact_basis": None,
                    "is_current_affairs": False,
                    "confidence": 0.0,
                }
                for i in range(slot_count)
            ]

    # ═════════════════════════════════════════════════════════
    # Step 5: Current affairs MCQs
    # ═════════════════════════════════════════════════════════
    async def _generate_current_affairs_mcqs(
        self,
        ca_question_count: int,
        prediction_date: date,
        start_number: int = 1,
    ) -> list[dict[str, Any]]:
        """Generate MCQs from top-scoring current affairs items (past 60–90 days)."""

        cutoff_start = prediction_date - timedelta(days=CURRENT_AFFAIRS_DAYS_MAX)
        cutoff_end = prediction_date - timedelta(days=CURRENT_AFFAIRS_DAYS_MIN)

        # Wider range: from 90 days before prediction_date to now
        ca_items_q = (
            select(CurrentAffairsItem)
            .where(
                CurrentAffairsItem.published_date >= cutoff_start,
                CurrentAffairsItem.relevance_score > 0.5,
            )
            .order_by(CurrentAffairsItem.relevance_score.desc())
            .limit(ca_question_count * 3)  # fetch more than needed for GPT selection
        )
        ca_items = (await self.db.execute(ca_items_q)).scalars().all()

        if not ca_items:
            logger.info("No current affairs items found for prediction date %s", prediction_date)
            return []

        # Build context for GPT
        ca_context = ""
        for i, item in enumerate(ca_items, 1):
            ca_context += f"\n--- Item {i} (score: {item.relevance_score:.2f}) ---\n"
            ca_context += f"Headline: {item.headline}\n"
            ca_context += f"Category: {item.category}\n"
            ca_context += f"Date: {item.published_date}\n"
            ca_context += f"Content: {item.content[:500]}\n"

        system_prompt = f"""You are a PPSC current affairs question designer.

Generate {ca_question_count} MCQs from the current affairs items below.
Focus on items most likely to appear in PPSC exams (government decisions,
national events, international summits, Pakistan-specific news).

Return ONLY valid JSON array:
[
  {{
    "question_text": "...",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_answer": "a",
    "subtopic": "category of current affair",
    "difficulty_score": 0.5,
    "fact_basis": "The specific fact tested",
    "confidence": 0.7
  }}
]"""

        try:
            response = await self.openai.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate {ca_question_count} current affairs MCQs from:\n{ca_context}"},
                ],
                call_type=OpenAICallType.PREDICTION_GENERATION,
                temperature=0.5,
                response_format={"type": "json_object"},
            )

            parsed = json.loads(response)
            questions_raw = parsed if isinstance(parsed, list) else parsed.get("questions", [])

            result: list[dict[str, Any]] = []
            for idx, q in enumerate(questions_raw[:ca_question_count]):
                result.append({
                    "question_number": start_number + idx,
                    "question_text": q.get("question_text", ""),
                    "option_a": q.get("option_a", ""),
                    "option_b": q.get("option_b", ""),
                    "option_c": q.get("option_c", ""),
                    "option_d": q.get("option_d", ""),
                    "correct_answer": q.get("correct_answer", "a"),
                    "topic_name": "Current Affairs",
                    "subtopic": q.get("subtopic"),
                    "difficulty_score": q.get("difficulty_score", 0.5),
                    "fact_basis": q.get("fact_basis"),
                    "is_current_affairs": True,
                    "confidence": q.get("confidence", 0.7),
                })

            # Mark CA items as included
            for item in ca_items[:len(result)]:
                item.is_included_in_prediction = True
                item.mcq_generated = True

            await self.db.flush()
            return result

        except Exception as exc:
            logger.exception("Current affairs MCQ generation failed: %s", exc)
            return []

    # ═════════════════════════════════════════════════════════
    # Step 6: Confidence scoring
    # ═════════════════════════════════════════════════════════
    async def _calculate_confidence(
        self,
        job_type_id: UUID,
        snapshot: PatternSnapshot | None = None,
    ) -> dict[str, Any]:
        """Calculate confidence_score based on paper count, pattern consistency, recency."""

        # Paper count for this job type
        paper_count_q = (
            select(func.count(Paper.id))
            .where(Paper.job_type_id == job_type_id, Paper.ingestion_status == "completed")
        )
        paper_count = (await self.db.execute(paper_count_q)).scalar() or 0

        # Recency of last paper
        latest_paper_q = (
            select(Paper.paper_year, Paper.paper_month)
            .where(Paper.job_type_id == job_type_id, Paper.ingestion_status == "completed")
            .order_by(Paper.paper_year.desc())
            .limit(1)
        )
        latest_paper = (await self.db.execute(latest_paper_q)).first()

        recency_score = 0.0
        if latest_paper:
            latest_year = latest_paper.paper_year
            latest_month = latest_paper.paper_month or 6
            latest_date = date(latest_year, latest_month, 1)
            days_since = (date.today() - latest_date).days
            # More recent → higher score; decays over 5 years (1825 days)
            recency_score = max(0.0, min(1.0, 1.0 - (days_since / 1825)))

        # Pattern consistency: how stable are the topic ratios?
        # Compare last 2 snapshots' topic distributions
        pattern_consistency = 0.5  # default medium
        if snapshot and snapshot.predicted_topic_ratios:
            prev_snapshot_q = (
                select(PatternSnapshot)
                .where(
                    PatternSnapshot.job_type_id == job_type_id,
                    PatternSnapshot.id != snapshot.id,
                )
                .order_by(PatternSnapshot.snapshot_date.desc())
                .limit(1)
            )
            prev_snapshot = (await self.db.execute(prev_snapshot_q)).scalar_one_or_none()

            if prev_snapshot and prev_snapshot.predicted_topic_ratios:
                # Calculate overlap between the two snapshots' topic distributions
                current_topics = set(snapshot.predicted_topic_ratios.keys())
                prev_topics = set(prev_snapshot.predicted_topic_ratios.keys())
                overlap = current_topics & prev_topics
                union = current_topics | prev_topics

                # Jaccard similarity for topic sets
                jaccard = len(overlap) / len(union) if union else 0.5

                # Also compare percentage distributions within overlapping topics
                pct_diff_sum = 0.0
                for topic in overlap:
                    curr_pct = float(snapshot.predicted_topic_ratios[topic].get("percentage", 0))
                    prev_pct = float(prev_snapshot.predicted_topic_ratios[topic].get("percentage", 0))
                    pct_diff_sum += abs(curr_pct - prev_pct)

                avg_pct_diff = pct_diff_sum / len(overlap) if overlap else 50
                distribution_similarity = max(0.0, 1.0 - (avg_pct_diff / 50))

                pattern_consistency = (jaccard * 0.4) + (distribution_similarity * 0.6)

        # Final confidence score (weighted combination)
        # paper_count weight: 40%, pattern_consistency: 35%, recency: 25%
        paper_count_factor = min(1.0, paper_count / 20)  # 20+ papers = max contribution
        confidence_score = round(
            (paper_count_factor * 0.40)
            + (pattern_consistency * 0.35)
            + (recency_score * 0.25),
            3,
        )
        # Clamp to [0.1, 0.95]
        confidence_score = max(0.1, min(0.95, confidence_score))

        return {
            "confidence_score": confidence_score,
            "paper_count": paper_count,
            "pattern_consistency": round(pattern_consistency, 3),
            "recency_score": round(recency_score, 3),
            "paper_count_factor": round(paper_count_factor, 3),
        }


# ── Convenience wrappers ─────────────────────────────────────

async def run_prediction_engine(
    db: AsyncSession,
    job_type_id: UUID,
    prediction_date: date,
    include_current_affairs: bool = True,
    total_questions: int = 100,
    openai: OpenAIService | None = None,
) -> dict[str, Any]:
    """Non-streaming entry point — runs the full pipeline and returns summary.

    Used by Celery tasks that don't stream.
    """
    engine = PredictionEngine(db, openai)
    result: dict[str, Any] = {}

    async for event in engine.generate_streaming(
        job_type_id=job_type_id,
        prediction_date=prediction_date,
        include_current_affairs=include_current_affairs,
        total_questions=total_questions,
    ):
        if event["event"] == "complete":
            result = event["data"]
        elif event["event"] == "error":
            result = {"status": "failed", **event["data"]}

    return result
