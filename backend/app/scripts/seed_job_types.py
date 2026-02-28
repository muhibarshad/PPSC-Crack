"""
Seed Script — Insert initial PPSC job types into the database.
================================================================
Run:  python -m app.scripts.seed_job_types
"""

import asyncio
import sys
from pathlib import Path

# Allow running from backend/ root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.database import async_session
from app.models.job_type import JobType
from sqlalchemy import select


SEED_JOB_TYPES = [
    {
        "name": "Clerk BS-11",
        "slug": "clerk-bs-11",
        "department": "General Administration",
        "topic_ratios": {
            "Pakistan Studies": 0.20,
            "General Knowledge": 0.20,
            "English": 0.15,
            "Mathematics": 0.15,
            "Urdu": 0.10,
            "Computer Science": 0.10,
            "Current Affairs": 0.10,
        },
    },
    {
        "name": "ASI Police",
        "slug": "asi-police",
        "department": "Punjab Police",
        "topic_ratios": {
            "Pakistan Studies": 0.15,
            "General Knowledge": 0.20,
            "English": 0.15,
            "Law & Constitution": 0.15,
            "Urdu": 0.10,
            "Islamiat": 0.10,
            "Current Affairs": 0.15,
        },
    },
    {
        "name": "Tehsildar",
        "slug": "tehsildar",
        "department": "Revenue Department",
        "topic_ratios": {
            "Pakistan Studies": 0.15,
            "General Knowledge": 0.15,
            "English": 0.15,
            "Land Revenue Act": 0.15,
            "Law & Constitution": 0.10,
            "Mathematics": 0.10,
            "Current Affairs": 0.10,
            "Urdu": 0.10,
        },
    },
    {
        "name": "School Teacher",
        "slug": "school-teacher",
        "department": "Education Department",
        "topic_ratios": {
            "Pakistan Studies": 0.15,
            "General Knowledge": 0.15,
            "English": 0.15,
            "Pedagogy & Teaching Methods": 0.20,
            "Urdu": 0.10,
            "Mathematics": 0.10,
            "Computer Science": 0.05,
            "Current Affairs": 0.10,
        },
    },
    {
        "name": "Finance Clerk",
        "slug": "finance-clerk",
        "department": "Finance Department",
        "topic_ratios": {
            "Accounting & Finance": 0.25,
            "General Knowledge": 0.15,
            "English": 0.15,
            "Mathematics": 0.15,
            "Pakistan Studies": 0.10,
            "Computer Science": 0.10,
            "Current Affairs": 0.10,
        },
    },
    {
        "name": "Forest Guard",
        "slug": "forest-guard",
        "department": "Forestry Department",
        "topic_ratios": {
            "Pakistan Studies": 0.15,
            "General Knowledge": 0.20,
            "English": 0.10,
            "Forestry & Environment": 0.20,
            "Urdu": 0.10,
            "Mathematics": 0.10,
            "Current Affairs": 0.15,
        },
    },
    {
        "name": "Patwari",
        "slug": "patwari",
        "department": "Revenue Department",
        "topic_ratios": {
            "Pakistan Studies": 0.15,
            "General Knowledge": 0.15,
            "English": 0.10,
            "Land Revenue & Administration": 0.20,
            "Mathematics": 0.15,
            "Urdu": 0.10,
            "Current Affairs": 0.15,
        },
    },
    {
        "name": "Junior Clerk",
        "slug": "junior-clerk",
        "department": "General Administration",
        "topic_ratios": {
            "Pakistan Studies": 0.20,
            "General Knowledge": 0.20,
            "English": 0.15,
            "Mathematics": 0.15,
            "Urdu": 0.10,
            "Computer Science": 0.10,
            "Current Affairs": 0.10,
        },
    },
]


async def seed() -> None:
    """Insert seed job types (skip if slug already exists)."""
    async with async_session() as db:
        inserted = 0
        skipped = 0

        for jt_data in SEED_JOB_TYPES:
            # Check if already exists
            result = await db.execute(
                select(JobType).where(JobType.slug == jt_data["slug"])
            )
            if result.scalar_one_or_none():
                print(f"  ⏭  {jt_data['name']} (already exists)")
                skipped += 1
                continue

            obj = JobType(**jt_data)
            db.add(obj)
            print(f"  ✅ {jt_data['name']}")
            inserted += 1

        await db.commit()
        print(f"\n🌱 Seed complete: {inserted} inserted, {skipped} skipped.")


def main() -> None:
    print("🌱 Seeding PPSC job types…\n")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
