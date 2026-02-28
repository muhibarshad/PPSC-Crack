"""
Seed Script — Insert core PPSC topics into the database.
============================================================
Run:  python -m app.scripts.seed_topics

Creates the standard set of topics that cover all PPSC exam categories
across all job types. Topics will be seeded with display names, default
colors, and initial metadata.
"""

import asyncio
import sys
from pathlib import Path

# Allow running from backend/ root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.database import async_session
from app.models.topic import Topic
from sqlalchemy import select


SEED_TOPICS = [
    # ── Core General ─────────────────────────────────────
    {
        "name": "Pakistan Studies",
        "display_name": "Pakistan Studies",
        "description": "History, geography, culture, independence movement, and political evolution of Pakistan.",
        "color_hex": "#8b5cf6",
        "icon": "flag",
    },
    {
        "name": "General Knowledge",
        "display_name": "General Knowledge",
        "description": "Wide-ranging questions covering world affairs, science, geography, culture, sports, and miscellaneous facts.",
        "color_hex": "#6366f1",
        "icon": "globe",
    },
    {
        "name": "Current Affairs",
        "display_name": "Current Affairs",
        "description": "Recent national and international events, government policies, appointments, and news highlights.",
        "color_hex": "#38bdf8",
        "icon": "newspaper",
    },
    {
        "name": "English",
        "display_name": "English",
        "description": "Grammar, vocabulary, comprehension, sentence correction, synonyms, antonyms, and idioms.",
        "color_hex": "#818cf8",
        "icon": "book",
    },
    {
        "name": "Urdu",
        "display_name": "Urdu",
        "description": "Urdu grammar, literature, poetry, idioms, proverbs, and comprehension.",
        "color_hex": "#34d399",
        "icon": "pen",
    },
    {
        "name": "Mathematics",
        "display_name": "Mathematics",
        "description": "Arithmetic, algebra, geometry, percentages, ratios, profit/loss, and quantitative reasoning.",
        "color_hex": "#fbbf24",
        "icon": "calculator",
    },
    {
        "name": "Computer Science",
        "display_name": "Computer Science",
        "description": "Basic computing, MS Office, internet, networking, data, hardware/software fundamentals.",
        "color_hex": "#e879f9",
        "icon": "monitor",
    },
    {
        "name": "Islamiat",
        "display_name": "Islamiat",
        "description": "Islamic history, teachings of the Prophet (PBUH), pillars of Islam, Quran, Hadith, and Islamic civilization.",
        "color_hex": "#a78bfa",
        "icon": "book-open",
    },

    # ── Specialized / Professional ───────────────────────
    {
        "name": "Law & Constitution",
        "display_name": "Law & Constitution",
        "description": "Pakistan Constitution (1973), fundamental rights, legal provisions, government structure, and amendments.",
        "color_hex": "#f87171",
        "icon": "scale",
    },
    {
        "name": "Pedagogy & Teaching Methods",
        "display_name": "Pedagogy & Teaching Methods",
        "description": "Teaching methodologies, classroom management, child psychology, assessment techniques, and education theory.",
        "color_hex": "#fb923c",
        "icon": "users",
    },
    {
        "name": "Accounting & Finance",
        "display_name": "Accounting & Finance",
        "description": "Basic accounting principles, bookkeeping, financial statements, budgeting, auditing, and public finance.",
        "color_hex": "#22d3ee",
        "icon": "wallet",
    },
    {
        "name": "Land Revenue Act",
        "display_name": "Land Revenue Act",
        "description": "Punjab Land Revenue Act 1967, revenue administration, land records, patwari system, and mutation procedures.",
        "color_hex": "#84cc16",
        "icon": "map",
    },
    {
        "name": "Land Revenue & Administration",
        "display_name": "Land Revenue & Administration",
        "description": "Revenue record management, settlement operations, land measurement, tenancy laws, and revenue courts.",
        "color_hex": "#a3e635",
        "icon": "map-pin",
    },
    {
        "name": "Forestry & Environment",
        "display_name": "Forestry & Environment",
        "description": "Forest management, wildlife protection, environmental science, climate change, and conservation policies.",
        "color_hex": "#4ade80",
        "icon": "tree",
    },
]


async def seed() -> None:
    """Insert seed topics (skip if name already exists)."""
    async with async_session() as db:
        inserted = 0
        skipped = 0

        for topic_data in SEED_TOPICS:
            # Check if already exists by unique name
            result = await db.execute(
                select(Topic).where(Topic.name == topic_data["name"])
            )
            if result.scalar_one_or_none():
                print(f"  ⏭  {topic_data['display_name']} (already exists)")
                skipped += 1
                continue

            obj = Topic(**topic_data)
            db.add(obj)
            print(f"  ✅ {topic_data['display_name']}")
            inserted += 1

        await db.commit()
        print(f"\n🌱 Seed complete: {inserted} inserted, {skipped} skipped.")


def main() -> None:
    print("🌱 Seeding PPSC topics…\n")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
