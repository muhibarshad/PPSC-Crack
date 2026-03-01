"""
Master Seed Script — Run all database seeders in order.
=========================================================
Run:  python -m app.scripts.seed_all

Seeds:
  1. Job Types          (8 PPSC job categories)
  2. Topics             (14 exam topics with colors & metadata)
  3. Papers             (10 sample past papers with ~1000 MCQs)
  4. Topic Frequencies  (year-by-year topic distribution analytics)
  5. Stories            (AI-generated narrative study docs per topic)
  6. Predictions        (4 AI-predicted papers for demo)
  7. Current Affairs    (10 recent news items with MCQs)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.scripts.seed_job_types import seed as seed_job_types
from app.scripts.seed_topics import seed as seed_topics
from app.scripts.seed_papers import seed as seed_papers
from app.scripts.seed_topic_frequencies import seed as seed_topic_frequencies
from app.scripts.seed_stories import seed as seed_stories
from app.scripts.seed_predictions import seed as seed_predictions
from app.scripts.seed_current_affairs import seed as seed_current_affairs


async def seed_all() -> None:
    print("═" * 50)
    print("  PPSC Crack — Database Seeder")
    print("═" * 50)

    print("\n📦 Step 1/7: Seeding Job Types…\n")
    await seed_job_types()

    print("\n📦 Step 2/7: Seeding Topics…\n")
    await seed_topics()

    print("\n📦 Step 3/7: Seeding Sample Papers & Questions…\n")
    await seed_papers()

    print("\n📦 Step 4/7: Seeding Topic Frequencies…\n")
    await seed_topic_frequencies()

    print("\n📦 Step 5/7: Seeding Topic Stories…\n")
    await seed_stories()

    print("\n📦 Step 6/7: Seeding AI Predictions…\n")
    await seed_predictions()

    print("\n📦 Step 7/7: Seeding Current Affairs…\n")
    await seed_current_affairs()

    print("\n" + "═" * 50)
    print("  ✅  All seeds completed!")
    print("═" * 50)


def main() -> None:
    asyncio.run(seed_all())


if __name__ == "__main__":
    main()
