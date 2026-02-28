"""
Master Seed Script — Run all database seeders in order.
=========================================================
Run:  python -m app.scripts.seed_all

Seeds:
  1. Job Types  (8 PPSC job categories)
  2. Topics     (14 exam topics with colors & metadata)
  3. Papers     (10 sample past papers with ~1000 MCQs)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.scripts.seed_job_types import seed as seed_job_types
from app.scripts.seed_topics import seed as seed_topics
from app.scripts.seed_papers import seed as seed_papers


async def seed_all() -> None:
    print("═" * 50)
    print("  PPSC Crack — Database Seeder")
    print("═" * 50)

    print("\n📦 Step 1/3: Seeding Job Types…\n")
    await seed_job_types()

    print("\n📦 Step 2/3: Seeding Topics…\n")
    await seed_topics()

    print("\n📦 Step 3/3: Seeding Sample Papers & Questions…\n")
    await seed_papers()

    print("\n" + "═" * 50)
    print("  ✅  All seeds completed!")
    print("═" * 50)


def main() -> None:
    asyncio.run(seed_all())


if __name__ == "__main__":
    main()
