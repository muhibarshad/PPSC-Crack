"""
Seed Script — Insert topic frequency data for analytics dashboards.
=====================================================================
Run:  python -m app.scripts.seed_topic_frequencies

Creates realistic year-by-year topic frequency data for each
job type × topic pair, powering the pattern analytics charts.
"""

import asyncio
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.database import async_session
from app.models.job_type import JobType
from app.models.topic import Topic
from app.models.topic_frequency import TopicFrequencyByJob
from sqlalchemy import select


# Base distribution templates per job type slug → topic weights
BASE_DISTRIBUTIONS: dict[str, dict[str, float]] = {
    "clerk-bs-11": {
        "Pakistan Studies": 0.20, "General Knowledge": 0.20, "English": 0.15,
        "Mathematics": 0.15, "Urdu": 0.10, "Computer Science": 0.10, "Current Affairs": 0.10,
    },
    "asi-police": {
        "Pakistan Studies": 0.15, "General Knowledge": 0.20, "English": 0.15,
        "Law & Constitution": 0.15, "Urdu": 0.10, "Islamiat": 0.10, "Current Affairs": 0.15,
    },
    "tehsildar": {
        "Pakistan Studies": 0.15, "General Knowledge": 0.15, "English": 0.15,
        "Land Revenue Act": 0.15, "Law & Constitution": 0.10, "Mathematics": 0.10,
        "Current Affairs": 0.10, "Urdu": 0.10,
    },
    "school-teacher": {
        "Pakistan Studies": 0.15, "General Knowledge": 0.15, "English": 0.15,
        "Pedagogy & Teaching Methods": 0.20, "Urdu": 0.10, "Mathematics": 0.10,
        "Computer Science": 0.05, "Current Affairs": 0.10,
    },
    "finance-clerk": {
        "Accounting & Finance": 0.25, "General Knowledge": 0.15, "English": 0.15,
        "Mathematics": 0.15, "Pakistan Studies": 0.10, "Computer Science": 0.10,
        "Current Affairs": 0.10,
    },
    "forest-guard": {
        "Pakistan Studies": 0.15, "General Knowledge": 0.20, "English": 0.10,
        "Forestry & Environment": 0.20, "Urdu": 0.10, "Mathematics": 0.10,
        "Current Affairs": 0.15,
    },
    "patwari": {
        "Pakistan Studies": 0.15, "General Knowledge": 0.15, "English": 0.10,
        "Land Revenue & Administration": 0.20, "Mathematics": 0.15, "Urdu": 0.10,
        "Current Affairs": 0.15,
    },
    "junior-clerk": {
        "Pakistan Studies": 0.20, "General Knowledge": 0.20, "English": 0.15,
        "Mathematics": 0.15, "Urdu": 0.10, "Computer Science": 0.10, "Current Affairs": 0.10,
    },
}

YEARS = list(range(2018, 2027))  # 2018-2026
QUESTIONS_PER_PAPER = 100


async def seed() -> None:
    """Insert topic frequency data for each job type × topic × year."""
    async with async_session() as db:
        jt_result = await db.execute(select(JobType))
        job_types = {jt.slug: jt for jt in jt_result.scalars().all()}

        topic_result = await db.execute(select(Topic))
        topics = {t.name: t for t in topic_result.scalars().all()}

        if not job_types or not topics:
            print("❌ Job types or topics missing. Run seed_job_types and seed_topics first.")
            return

        inserted = 0
        skipped = 0

        for jt_slug, dist in BASE_DISTRIBUTIONS.items():
            jt = job_types.get(jt_slug)
            if not jt:
                continue

            for year in YEARS:
                for topic_name, base_ratio in dist.items():
                    topic = topics.get(topic_name)
                    if not topic:
                        continue

                    # Check if already exists
                    existing = await db.execute(
                        select(TopicFrequencyByJob).where(
                            TopicFrequencyByJob.topic_id == topic.id,
                            TopicFrequencyByJob.job_type_id == jt.id,
                            TopicFrequencyByJob.year == year,
                        )
                    )
                    if existing.scalar_one_or_none():
                        skipped += 1
                        continue

                    # Add some year-over-year variance (±5%)
                    variance = random.uniform(-0.05, 0.05)
                    actual_ratio = max(0.02, min(0.40, base_ratio + variance))
                    q_count = round(actual_ratio * QUESTIONS_PER_PAPER)

                    obj = TopicFrequencyByJob(
                        topic_id=topic.id,
                        job_type_id=jt.id,
                        year=year,
                        question_count=q_count,
                        percentage_of_paper=round(actual_ratio * 100, 1),
                    )
                    db.add(obj)
                    inserted += 1

            print(f"  ✅ {jt.name}: {len(YEARS)} years × {len(dist)} topics")

        await db.commit()
        print(f"\n🌱 Topic frequencies seed: {inserted} inserted, {skipped} skipped.")


def main() -> None:
    print("🌱 Seeding Topic Frequencies…\n")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
