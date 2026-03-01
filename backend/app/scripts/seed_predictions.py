"""
Seed Script — Insert sample AI predictions for demo purposes.
================================================================
Run:  python -m app.scripts.seed_predictions

Creates sample predicted papers for several job types to populate
the Prediction Studio and student predicted paper views.
"""

import asyncio
import json
import random
import sys
from datetime import datetime, timezone, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.database import async_session
from app.models.job_type import JobType
from app.models.prediction import Prediction
from sqlalchemy import select


# ── Sample predicted MCQs (compact form) ─────────────────────

PREDICTED_MCQS = {
    "Pakistan Studies": [
        {"question_text": "The Simla Deputation of 1906 was led by:", "options": {"a": "Sir Syed Ahmed Khan", "b": "Sir Agha Khan", "c": "Allama Iqbal", "d": "Quaid-e-Azam"}, "correct_answer": "b", "topic_name": "Pakistan Studies", "difficulty": "medium"},
        {"question_text": "The Objective Resolution was passed in:", "options": {"a": "1947", "b": "1949", "c": "1951", "d": "1953"}, "correct_answer": "b", "topic_name": "Pakistan Studies", "difficulty": "easy"},
        {"question_text": "K2 is the ___ highest mountain in the world:", "options": {"a": "1st", "b": "2nd", "c": "3rd", "d": "4th"}, "correct_answer": "b", "topic_name": "Pakistan Studies", "difficulty": "easy"},
        {"question_text": "The Tarbela Dam is built on which river?", "options": {"a": "Jhelum", "b": "Chenab", "c": "Indus", "d": "Ravi"}, "correct_answer": "c", "topic_name": "Pakistan Studies", "difficulty": "medium"},
        {"question_text": "Who wrote the national anthem of Pakistan?", "options": {"a": "Allama Iqbal", "b": "Faiz Ahmed Faiz", "c": "Hafeez Jalandhari", "d": "Ahmed Faraz"}, "correct_answer": "c", "topic_name": "Pakistan Studies", "difficulty": "easy"},
    ],
    "General Knowledge": [
        {"question_text": "The Sahara Desert is located in which continent?", "options": {"a": "Asia", "b": "Africa", "c": "South America", "d": "Australia"}, "correct_answer": "b", "topic_name": "General Knowledge", "difficulty": "easy"},
        {"question_text": "Which gas is most abundant in Earth's atmosphere?", "options": {"a": "Oxygen", "b": "Carbon Dioxide", "c": "Nitrogen", "d": "Hydrogen"}, "correct_answer": "c", "topic_name": "General Knowledge", "difficulty": "easy"},
        {"question_text": "The Great Wall of China is approximately how many km long?", "options": {"a": "5,000", "b": "10,000", "c": "15,000", "d": "21,000"}, "correct_answer": "d", "topic_name": "General Knowledge", "difficulty": "medium"},
        {"question_text": "Which vitamin is produced by sunlight?", "options": {"a": "Vitamin A", "b": "Vitamin B", "c": "Vitamin C", "d": "Vitamin D"}, "correct_answer": "d", "topic_name": "General Knowledge", "difficulty": "easy"},
    ],
    "English": [
        {"question_text": "The idiom 'Break the ice' means:", "options": {"a": "Destroy something", "b": "Start a conversation", "c": "Cool down", "d": "Fight"}, "correct_answer": "b", "topic_name": "English", "difficulty": "medium"},
        {"question_text": "Choose the correct passive voice: 'She writes a letter'", "options": {"a": "A letter is written by her", "b": "A letter was written by her", "c": "A letter is being written by her", "d": "A letter has been written by her"}, "correct_answer": "a", "topic_name": "English", "difficulty": "medium"},
        {"question_text": "The antonym of 'Affluent' is:", "options": {"a": "Wealthy", "b": "Poor", "c": "Rich", "d": "Prosperous"}, "correct_answer": "b", "topic_name": "English", "difficulty": "easy"},
    ],
    "Mathematics": [
        {"question_text": "A man buys an article for Rs. 800 and sells it for Rs. 1000. Profit %?", "options": {"a": "20%", "b": "25%", "c": "30%", "d": "15%"}, "correct_answer": "b", "topic_name": "Mathematics", "difficulty": "medium"},
        {"question_text": "The LCM of 12, 15, and 20 is:", "options": {"a": "30", "b": "60", "c": "120", "d": "180"}, "correct_answer": "b", "topic_name": "Mathematics", "difficulty": "medium"},
        {"question_text": "If a circle has radius 7cm, its area is:", "options": {"a": "144 cm²", "b": "154 cm²", "c": "164 cm²", "d": "174 cm²"}, "correct_answer": "b", "topic_name": "Mathematics", "difficulty": "medium"},
    ],
    "Current Affairs": [
        {"question_text": "Which country is the largest producer of oil in 2025?", "options": {"a": "Saudi Arabia", "b": "Russia", "c": "United States", "d": "China"}, "correct_answer": "c", "topic_name": "Current Affairs", "difficulty": "medium", "is_current_affairs": True},
        {"question_text": "The SCO Summit 2025 was hosted by:", "options": {"a": "India", "b": "China", "c": "Pakistan", "d": "Russia"}, "correct_answer": "b", "topic_name": "Current Affairs", "difficulty": "medium", "is_current_affairs": True},
        {"question_text": "Pakistan's GDP growth rate in FY 2024-25 is estimated at:", "options": {"a": "1.5%", "b": "2.5%", "c": "3.5%", "d": "4.5%"}, "correct_answer": "c", "topic_name": "Current Affairs", "difficulty": "hard", "is_current_affairs": True},
    ],
}

# ── Prediction templates ─────────────────────────────────────

PREDICTION_TEMPLATES = [
    {
        "job_slug": "clerk-bs-11",
        "title": "AI Predicted Paper — Clerk BS-11 (July 2026)",
        "pred_date": "2026-07-01",
        "total_questions": 100,
        "topics_to_use": ["Pakistan Studies", "General Knowledge", "English", "Mathematics", "Current Affairs"],
        "confidence": 0.78,
        "paper_basis": 8,
        "pattern_consistency": 0.82,
        "status": "published",
        "is_published": True,
    },
    {
        "job_slug": "asi-police",
        "title": "AI Predicted Paper — ASI Police (August 2026)",
        "pred_date": "2026-08-01",
        "total_questions": 100,
        "topics_to_use": ["Pakistan Studies", "General Knowledge", "English", "Current Affairs"],
        "confidence": 0.72,
        "paper_basis": 6,
        "pattern_consistency": 0.75,
        "status": "published",
        "is_published": True,
    },
    {
        "job_slug": "tehsildar",
        "title": "AI Predicted Paper — Tehsildar (September 2026)",
        "pred_date": "2026-09-01",
        "total_questions": 100,
        "topics_to_use": ["Pakistan Studies", "General Knowledge", "English", "Mathematics"],
        "confidence": 0.65,
        "paper_basis": 4,
        "pattern_consistency": 0.68,
        "status": "completed",
        "is_published": False,
    },
    {
        "job_slug": "school-teacher",
        "title": "AI Predicted Paper — School Teacher (July 2026)",
        "pred_date": "2026-07-01",
        "total_questions": 100,
        "topics_to_use": ["Pakistan Studies", "General Knowledge", "English", "Mathematics", "Current Affairs"],
        "confidence": 0.81,
        "paper_basis": 7,
        "pattern_consistency": 0.85,
        "status": "published",
        "is_published": True,
    },
]


def _build_prediction_questions(topic_names: list[str], total: int) -> tuple[list, list]:
    """Build question and current affairs lists from templates."""
    questions = []
    current_affairs = []
    q_num = 1

    topics_available = [t for t in topic_names if t in PREDICTED_MCQS]
    per_topic = max(1, total // max(len(topics_available), 1))

    for topic in topics_available:
        pool = PREDICTED_MCQS[topic]
        selected = pool * ((per_topic // len(pool)) + 1)  # repeat if needed
        selected = selected[:per_topic]

        for q in selected:
            item = {**q, "question_number": q_num}
            if q.get("is_current_affairs"):
                current_affairs.append(item)
            else:
                questions.append(item)
            q_num += 1

    return questions[:total], current_affairs


async def seed() -> None:
    """Insert sample predictions."""
    async with async_session() as db:
        jt_result = await db.execute(select(JobType))
        job_types = {jt.slug: jt for jt in jt_result.scalars().all()}

        if not job_types:
            print("❌ No job types found. Run seed_job_types first.")
            return

        inserted = 0
        skipped = 0

        for tmpl in PREDICTION_TEMPLATES:
            jt = job_types.get(tmpl["job_slug"])
            if not jt:
                print(f"  ⏭  Skipping — job type '{tmpl['job_slug']}' not found")
                skipped += 1
                continue

            # Check if already exists
            existing = await db.execute(
                select(Prediction).where(
                    Prediction.job_type_id == jt.id,
                    Prediction.title == tmpl["title"],
                )
            )
            if existing.scalar_one_or_none():
                print(f"  ⏭  {tmpl['title']} (already exists)")
                skipped += 1
                continue

            questions, ca_questions = _build_prediction_questions(
                tmpl["topics_to_use"], tmpl["total_questions"]
            )

            # Topic distribution
            topic_dist = {}
            for t in tmpl["topics_to_use"]:
                topic_dist[t] = len([q for q in questions if q.get("topic_name") == t])

            pred = Prediction(
                job_type_id=jt.id,
                title=tmpl["title"],
                prediction_date=date.fromisoformat(tmpl["pred_date"]),
                total_questions=tmpl["total_questions"],
                include_current_affairs=True,
                questions_json={"questions": questions},
                current_affairs_json={"questions": ca_questions},
                topic_distribution=topic_dist,
                generation_metadata={
                    "model": "ppsc-predict-v2",
                    "algorithm": "weighted_frequency_analysis",
                    "seeded": True,
                },
                confidence_score=tmpl["confidence"],
                paper_count_basis=tmpl["paper_basis"],
                pattern_consistency=tmpl["pattern_consistency"],
                status=tmpl["status"],
                is_published=tmpl["is_published"],
                published_at=datetime.now(timezone.utc) if tmpl["is_published"] else None,
            )
            db.add(pred)
            print(f"  ✅ {tmpl['title']} ({len(questions)} Qs, {len(ca_questions)} CA)")
            inserted += 1

        await db.commit()
        print(f"\n🌱 Predictions seed: {inserted} inserted, {skipped} skipped.")


def main() -> None:
    print("🌱 Seeding AI Predictions…\n")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
