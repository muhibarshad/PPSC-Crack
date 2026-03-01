"""
Seed Script — Populate topics with story documents for story-based learning.
==============================================================================
Run:  python -m app.scripts.seed_stories

Adds AI-style narrative story documents to each topic for the
story-based learning feature on the student dashboard.
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.database import async_session
from app.models.topic import Topic
from sqlalchemy import select


TOPIC_STORIES: dict[str, str] = {
    "Pakistan Studies": """# Pakistan Studies — The Complete Story

## The Birth of a Nation (1947)

The story of Pakistan begins long before the midnight of August 14, 1947. It is a tale of vision, sacrifice, and the unwavering determination of millions who believed in the dream of a separate Muslim homeland.

### The Two-Nation Theory
Sir Syed Ahmed Khan was among the first to articulate that Hindus and Muslims were two distinct nations with different religions, philosophies, and social customs. This became the intellectual foundation of the Pakistan Movement.

### Key Milestones
- **1906** — The All-India Muslim League was founded in Dhaka
- **1930** — Allama Iqbal's historic Allahabad Address envisioned a Muslim state in northwest India
- **1940** — The Lahore Resolution (Pakistan Resolution) formally demanded separate Muslim states
- **1947** — Pakistan achieved independence on August 14th

### The Constitution Journey
Pakistan's constitutional evolution has been turbulent:
1. **1956** — First Constitution (Islamic Republic)
2. **1962** — Second Constitution (Presidential system)
3. **1973** — Third Constitution (Parliamentary system, still in force)

### Geography & Resources
Pakistan spans 881,913 km² with diverse geography from the Karakoram mountains (K2, 8,611m) to the Arabian Sea coast. Key resources include agriculture (Punjab's fertile plains), minerals (Balochistan's copper-gold deposits at Reko Diq), and strategic ports (Gwadar).

> **PPSC Tip:** Questions on the 1973 Constitution's articles (especially Fundamental Rights in Part II) appear in almost every exam. Focus on Articles 8-28.""",

    "General Knowledge": """# General Knowledge — The Essential Encyclopedia

## World Geography
- **Largest Ocean:** Pacific Ocean (165.25 million km²)
- **Longest River:** Nile River (6,650 km)
- **Highest Mountain:** Mount Everest (8,849 m)
- **Largest Desert:** Sahara (9.2 million km²)
- **Deepest Ocean Point:** Mariana Trench (11,034 m)

## Science Fundamentals
The periodic table contains 118 confirmed elements. Key facts:
- Gold (Au), Silver (Ag), Iron (Fe), Copper (Cu)
- Speed of light: 299,792 km/s
- Water boils at 100°C, freezes at 0°C (at sea level)
- DNA carries genetic information; RNA translates it

## World Organizations
| Organization | Founded | HQ | Members |
|---|---|---|---|
| United Nations | 1945 | New York | 193 |
| WHO | 1948 | Geneva | 194 |
| IMF | 1944 | Washington DC | 190 |
| OIC | 1969 | Jeddah | 57 |

> **PPSC Tip:** GK questions form 15-20% of most PPSC papers. Focus on "firsts," "largests," and international organizations.""",

    "Current Affairs": """# Current Affairs — Staying Ahead of the Exam

## Why Current Affairs Matter
Current Affairs questions typically make up 10-15% of PPSC papers. They test awareness of recent national and international events from the last 6-12 months.

## Key Areas to Watch
1. **Government Appointments** — New ministers, judges, military chiefs
2. **International Agreements** — Trade deals, treaties, summits
3. **Economic Indicators** — GDP, inflation rate, SBP policy rate
4. **Sports** — Cricket, hockey, Olympics results
5. **Awards & Honors** — Nobel Prize, national awards

## Strategy
- Read Dawn, Geo, and The News daily
- Focus on Pakistan-specific news
- Track IMF reviews, CPEC updates, and bilateral relations
- Note exact figures (budget amounts, population data)

> **PPSC Tip:** Current affairs from the last 3 months before the exam are most heavily tested.""",

    "English": """# English — Grammar, Vocabulary & Comprehension

## Grammar Essentials

### Tenses (Most Tested)
| Tense | Structure | Example |
|---|---|---|
| Simple Present | S + V1 | She writes daily |
| Present Continuous | S + is/am/are + V-ing | She is writing |
| Simple Past | S + V2 | She wrote yesterday |
| Past Perfect | S + had + V3 | She had written |

### Active vs Passive Voice
- Active: "The cat catches the mouse"
- Passive: "The mouse is caught by the cat"

### Direct vs Indirect Speech
- Direct: He said, "I am going."
- Indirect: He said that he was going.

## Vocabulary Power
### Common Synonyms (PPSC Favorites)
- Abandon → Forsake, Relinquish
- Benevolent → Kind, Charitable
- Diligent → Hardworking, Industrious
- Gregarious → Sociable, Outgoing

> **PPSC Tip:** Focus on sentence correction, synonyms/antonyms, and idioms. These three areas cover 60% of English questions.""",

    "Mathematics": """# Mathematics — Quantitative Reasoning & Arithmetic

## Core Formulas

### Percentages
- Percentage = (Part / Whole) × 100
- Percentage Change = ((New - Old) / Old) × 100

### Profit & Loss
- Profit % = (Profit / Cost Price) × 100
- Selling Price = CP × (1 + Profit%/100)

### Time, Speed & Distance
- Speed = Distance / Time
- Average Speed = 2 × S1 × S2 / (S1 + S2)

### Simple & Compound Interest
- SI = P × R × T / 100
- CI = P(1 + R/100)^T - P

## Number Series Patterns
Look for: +2, ×2, alternate operations, squares, cubes, primes

> **PPSC Tip:** Practice mental math. Most PPSC math can be solved in 30 seconds with shortcut methods.""",

    "Islamiat": """# Islamiat — Islamic Studies Essentials

## Five Pillars of Islam
1. **Shahada** — Declaration of faith
2. **Salah** — Five daily prayers
3. **Zakat** — Annual charity (2.5% of wealth)
4. **Sawm** — Fasting during Ramadan
5. **Hajj** — Pilgrimage to Makkah

## The Holy Quran
- **Total Surahs:** 114
- **Total Ayahs:** 6,236
- **Longest Surah:** Al-Baqarah (286 ayahs)
- **Shortest Surah:** Al-Kawthar (3 ayahs)
- **Revelation Period:** 23 years (610-632 CE)

## Key Battles
| Battle | Year | Significance |
|---|---|---|
| Badr | 2 AH (624 CE) | First major victory |
| Uhud | 3 AH (625 CE) | Lesson in obedience |
| Khandaq | 5 AH (627 CE) | Siege warfare/trench |
| Conquest of Makkah | 8 AH (630 CE) | Peaceful conquest |

> **PPSC Tip:** Islamiat appears in almost every PPSC exam. Focus on Quranic facts, prophetic biography, and the Khulafa-e-Rashideen.""",

    "Computer Science": """# Computer Science — Digital Literacy Essentials

## Hardware vs Software
- **Hardware:** Physical components (CPU, RAM, HDD, Monitor)
- **Software:** Programs (OS, Applications, Utilities)

## Key Concepts
### Memory Hierarchy
1. **Registers** (fastest, smallest)
2. **Cache** (L1, L2, L3)
3. **RAM** (volatile, fast)
4. **SSD/HDD** (non-volatile, storage)

### Units of Data
- 1 Byte = 8 Bits
- 1 KB = 1,024 Bytes
- 1 MB = 1,024 KB
- 1 GB = 1,024 MB
- 1 TB = 1,024 GB

### MS Office Shortcuts (PPSC Favorite!)
| Shortcut | Action |
|---|---|
| Ctrl+C | Copy |
| Ctrl+V | Paste |
| Ctrl+S | Save |
| Ctrl+Z | Undo |
| Ctrl+P | Print |
| Ctrl+F | Find |

> **PPSC Tip:** MS Office questions are guaranteed. Know Word, Excel, and PowerPoint shortcuts and features.""",

    "Urdu": """# Urdu — Grammar, Literature & Poetry

## Urdu Grammar (قواعد)
### Parts of Speech
- **اسم** (Noun) — نام
- **فعل** (Verb) — کام
- **صفت** (Adjective) — خوبصورت
- **حرف** (Preposition) — میں، پر، سے

## Famous Poets & Works
| Poet | Famous Work | Era |
|---|---|---|
| Mirza Ghalib | Diwan-e-Ghalib | 1797-1869 |
| Allama Iqbal | Bang-e-Dara | 1877-1938 |
| Faiz Ahmed Faiz | Naqsh-e-Faryadi | 1911-1984 |
| Ahmed Faraz | Tanha Tanha | 1931-2008 |

## Common Idioms (محاورے)
- آنکھیں کھلنا — to realize
- ناک میں دم کرنا — to harass
- ہاتھ ملنا — to repent
- دال میں کچھ کالا — something suspicious

> **PPSC Tip:** Focus on muhawre (idioms), zarb-ul-misal (proverbs), and the works of major Urdu poets.""",

    "Law & Constitution": """# Law & Constitution — Pakistan's Legal Framework

## The Constitution of Pakistan 1973
The current Constitution was adopted on April 12, 1973 and enforced on August 14, 1973.

### Structure
- **Preamble** — Objectives Resolution
- **Part I** — Introductory (Articles 1-6)
- **Part II** — Fundamental Rights (Articles 8-28)
- **Part III** — Federation (Articles 29-100)
- **Part IV** — Provinces (Articles 101-140A)
- **Schedules** — 5 schedules

### Key Articles (PPSC Favorites)
| Article | Subject |
|---|---|
| Article 1 | Name and Territory of Pakistan |
| Article 8 | Laws inconsistent with fundamental rights void |
| Article 10 | Right to fair trial |
| Article 14 | Right to privacy |
| Article 17 | Freedom of association |
| Article 19 | Freedom of speech |
| Article 19-A | Right to information |
| Article 25 | Equality before law |

### Constitutional Amendments
There have been 26 amendments to the 1973 Constitution. The most significant:
- **18th Amendment (2010)** — Provincial autonomy, renamed NWFP to KPK
- **21st Amendment (2015)** — Military courts for terrorism cases
- **25th Amendment (2018)** — FATA merged with KPK

> **PPSC Tip:** Articles 8-28 (Fundamental Rights) are the most tested. Know them by number.""",
}


async def seed() -> None:
    """Update topics with story documents."""
    async with async_session() as db:
        updated = 0
        skipped = 0

        for topic_name, story in TOPIC_STORIES.items():
            result = await db.execute(
                select(Topic).where(Topic.name == topic_name)
            )
            topic = result.scalar_one_or_none()
            if not topic:
                print(f"  ⏭  {topic_name} — topic not found")
                skipped += 1
                continue

            if topic.story_document and len(topic.story_document) > 100:
                print(f"  ⏭  {topic_name} — story already exists ({topic.story_word_count} words)")
                skipped += 1
                continue

            topic.story_document = story
            topic.story_word_count = len(story.split())
            topic.story_last_updated = datetime.now(timezone.utc)

            print(f"  ✅ {topic_name} — {topic.story_word_count} words")
            updated += 1

        await db.commit()
        print(f"\n🌱 Stories seed: {updated} updated, {skipped} skipped.")


def main() -> None:
    print("🌱 Seeding Topic Stories…\n")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
