"""
Seed Script — Insert sample PPSC past papers & MCQ questions.
================================================================
Run:  python -m app.scripts.seed_papers

Creates realistic sample papers for several job types with
questions across multiple topics for demo / development use.
"""

import asyncio
import random
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.database import async_session
from app.models.job_type import JobType
from app.models.paper import Paper
from app.models.question import Question
from app.models.topic import Topic
from sqlalchemy import select, func

# ── Sample MCQs by topic (realistic PPSC-style) ─────────────

SAMPLE_QUESTIONS: dict[str, list[dict]] = {
    "Pakistan Studies": [
        {"q": "Who was the first Governor-General of Pakistan?", "a": "Quaid-e-Azam Muhammad Ali Jinnah", "b": "Liaquat Ali Khan", "c": "Khawaja Nazimuddin", "d": "Iskander Mirza", "ans": "a"},
        {"q": "The Lahore Resolution was passed in which year?", "a": "1935", "b": "1940", "c": "1947", "d": "1930", "ans": "b"},
        {"q": "Which city is known as the 'City of Saints'?", "a": "Lahore", "b": "Peshawar", "c": "Multan", "d": "Karachi", "ans": "c"},
        {"q": "The Indus Water Treaty was signed in:", "a": "1958", "b": "1960", "c": "1962", "d": "1965", "ans": "b"},
        {"q": "Who presented the Fourteen Points?", "a": "Allama Iqbal", "b": "Quaid-e-Azam", "c": "Liaquat Ali Khan", "d": "Sir Syed Ahmed Khan", "ans": "b"},
        {"q": "The longest river of Pakistan is:", "a": "Jhelum", "b": "Chenab", "c": "Indus", "d": "Ravi", "ans": "c"},
        {"q": "Pakistan became a republic in:", "a": "1947", "b": "1954", "c": "1956", "d": "1962", "ans": "c"},
        {"q": "Who was the first Prime Minister of Pakistan?", "a": "Quaid-e-Azam", "b": "Liaquat Ali Khan", "c": "Khawaja Nazimuddin", "d": "Feroz Khan Noon", "ans": "b"},
    ],
    "General Knowledge": [
        {"q": "Which planet is known as the Red Planet?", "a": "Venus", "b": "Jupiter", "c": "Mars", "d": "Saturn", "ans": "c"},
        {"q": "The largest ocean in the world is:", "a": "Atlantic", "b": "Indian", "c": "Arctic", "d": "Pacific", "ans": "d"},
        {"q": "The chemical symbol for Gold is:", "a": "Au", "b": "Ag", "c": "Fe", "d": "Cu", "ans": "a"},
        {"q": "Who invented the telephone?", "a": "Thomas Edison", "b": "Alexander Graham Bell", "c": "Nikola Tesla", "d": "Guglielmo Marconi", "ans": "b"},
        {"q": "The United Nations was established in:", "a": "1944", "b": "1945", "c": "1946", "d": "1948", "ans": "b"},
        {"q": "Which is the largest country by area?", "a": "China", "b": "USA", "c": "Canada", "d": "Russia", "ans": "d"},
        {"q": "The currency of Japan is:", "a": "Yuan", "b": "Won", "c": "Yen", "d": "Ringgit", "ans": "c"},
        {"q": "Which blood group is universal donor?", "a": "A+", "b": "B+", "c": "AB+", "d": "O-", "ans": "d"},
    ],
    "English": [
        {"q": "Choose the correct spelling:", "a": "Accomodation", "b": "Accommodation", "c": "Acomodation", "d": "Acommodation", "ans": "b"},
        {"q": "The synonym of 'Benevolent' is:", "a": "Cruel", "b": "Kind", "c": "Wealthy", "d": "Brave", "ans": "b"},
        {"q": "She ___ to school every day.", "a": "go", "b": "goes", "c": "going", "d": "gone", "ans": "b"},
        {"q": "The antonym of 'Abundant' is:", "a": "Plentiful", "b": "Copious", "c": "Scarce", "d": "Ample", "ans": "c"},
        {"q": "'To cry over spilt milk' means:", "a": "To waste milk", "b": "To regret uselessly", "c": "To be happy", "d": "To clean up", "ans": "b"},
        {"q": "Choose the correct sentence:", "a": "He don't know", "b": "He doesn't knows", "c": "He doesn't know", "d": "He don't knows", "ans": "c"},
    ],
    "Mathematics": [
        {"q": "What is 15% of 200?", "a": "25", "b": "30", "c": "35", "d": "40", "ans": "b"},
        {"q": "If x + 5 = 12, then x = ?", "a": "5", "b": "6", "c": "7", "d": "8", "ans": "c"},
        {"q": "The HCF of 12 and 18 is:", "a": "2", "b": "4", "c": "6", "d": "8", "ans": "c"},
        {"q": "A train 100m long passes a pole in 10 seconds. Its speed is:", "a": "36 km/h", "b": "30 km/h", "c": "40 km/h", "d": "25 km/h", "ans": "a"},
        {"q": "The square root of 144 is:", "a": "11", "b": "12", "c": "13", "d": "14", "ans": "b"},
        {"q": "If 3x = 27, then x = ?", "a": "7", "b": "8", "c": "9", "d": "10", "ans": "c"},
    ],
    "Current Affairs": [
        {"q": "Which country hosted the 2022 FIFA World Cup?", "a": "Russia", "b": "Qatar", "c": "Brazil", "d": "France", "ans": "b"},
        {"q": "Pakistan's National Security Policy was launched in:", "a": "2020", "b": "2021", "c": "2022", "d": "2023", "ans": "c"},
        {"q": "CPEC stands for:", "a": "China-Pakistan Economic Corridor", "b": "Central Pakistan Economic Commission", "c": "China-Punjab Energy Compact", "d": "Central Pakistan Energy Corridor", "ans": "a"},
        {"q": "The Paris Climate Agreement was adopted in:", "a": "2013", "b": "2014", "c": "2015", "d": "2016", "ans": "c"},
        {"q": "Who is the current Secretary-General of the United Nations?", "a": "Ban Ki-moon", "b": "Kofi Annan", "c": "António Guterres", "d": "Boutros Boutros-Ghali", "ans": "c"},
    ],
    "Islamiat": [
        {"q": "How many Surahs are in the Holy Quran?", "a": "110", "b": "112", "c": "114", "d": "116", "ans": "c"},
        {"q": "The first revelation was received in:", "a": "Masjid al-Haram", "b": "Cave of Hira", "c": "Cave of Thawr", "d": "Masjid al-Nabawi", "ans": "b"},
        {"q": "The battle of Badr was fought in:", "a": "1 AH", "b": "2 AH", "c": "3 AH", "d": "4 AH", "ans": "b"},
        {"q": "How many pillars of Islam are there?", "a": "3", "b": "4", "c": "5", "d": "6", "ans": "c"},
        {"q": "The longest Surah of the Quran is:", "a": "Al-Imran", "b": "Al-Baqarah", "c": "An-Nisa", "d": "Al-Maidah", "ans": "b"},
    ],
    "Urdu": [
        {"q": "'اردو' کا لفظی معنی کیا ہے؟", "a": "فوج", "b": "لشکر", "c": "بازار", "d": "زبان", "ans": "b"},
        {"q": "علامہ اقبال کا پہلا اردو شعری مجموعہ:", "a": "بانگِ درا", "b": "بالِ جبریل", "c": "ضربِ کلیم", "d": "ارمغانِ حجاز", "ans": "a"},
        {"q": "'محاورہ' نکل بھاگنا کا مطلب:", "a": "آنا", "b": "فرار ہونا", "c": "سونا", "d": "کھانا", "ans": "b"},
        {"q": "مرزا غالب کا اصل نام کیا تھا؟", "a": "اسد اللہ خان", "b": "محمد خان", "c": "احمد خان", "d": "علی خان", "ans": "a"},
    ],
    "Computer Science": [
        {"q": "CPU stands for:", "a": "Central Processing Unit", "b": "Central Program Utility", "c": "Computer Personal Unit", "d": "Central Peripheral Unit", "ans": "a"},
        {"q": "Which is not an operating system?", "a": "Windows", "b": "Linux", "c": "Oracle", "d": "macOS", "ans": "c"},
        {"q": "RAM stands for:", "a": "Random Access Memory", "b": "Read Access Memory", "c": "Run Access Memory", "d": "Random Allocated Memory", "ans": "a"},
        {"q": "1 KB equals:", "a": "1000 bytes", "b": "1024 bytes", "c": "512 bytes", "d": "2048 bytes", "ans": "b"},
        {"q": "Which shortcut is used to copy text?", "a": "Ctrl+V", "b": "Ctrl+X", "c": "Ctrl+C", "d": "Ctrl+Z", "ans": "c"},
    ],
    "Law & Constitution": [
        {"q": "The Constitution of Pakistan 1973 has how many Articles?", "a": "240", "b": "260", "c": "280", "d": "300", "ans": "c"},
        {"q": "Fundamental Rights in the 1973 Constitution are in:", "a": "Part I", "b": "Part II", "c": "Part III", "d": "Part IV", "ans": "b"},
        {"q": "The minimum age for the President of Pakistan is:", "a": "35 years", "b": "40 years", "c": "45 years", "d": "50 years", "ans": "c"},
        {"q": "How many schedules are in the 1973 Constitution?", "a": "4", "b": "5", "c": "6", "d": "7", "ans": "b"},
    ],
}

# ── Paper templates ──────────────────────────────────────────

PAPER_TEMPLATES = [
    # (title_template, job_type_slug, year, month, topics_to_use, num_questions)
    ("Clerk BS-11 — Past Paper {year}", "clerk-bs-11", 2024, 3, ["Pakistan Studies", "General Knowledge", "English", "Mathematics", "Current Affairs", "Computer Science", "Urdu"], 100),
    ("Clerk BS-11 — Past Paper {year}", "clerk-bs-11", 2023, 9, ["Pakistan Studies", "General Knowledge", "English", "Mathematics", "Islamiat", "Computer Science"], 100),
    ("Clerk BS-11 — Past Paper {year}", "clerk-bs-11", 2022, 6, ["Pakistan Studies", "General Knowledge", "English", "Mathematics", "Current Affairs", "Urdu"], 100),
    ("ASI Police — Past Paper {year}", "asi-police", 2024, 1, ["Pakistan Studies", "General Knowledge", "English", "Law & Constitution", "Islamiat", "Current Affairs"], 100),
    ("ASI Police — Past Paper {year}", "asi-police", 2023, 5, ["Pakistan Studies", "General Knowledge", "English", "Law & Constitution", "Current Affairs", "Urdu"], 100),
    ("Tehsildar — Past Paper {year}", "tehsildar", 2024, 2, ["Pakistan Studies", "General Knowledge", "English", "Mathematics", "Current Affairs", "Law & Constitution"], 100),
    ("School Teacher — Past Paper {year}", "school-teacher", 2023, 11, ["Pakistan Studies", "General Knowledge", "English", "Mathematics", "Urdu", "Islamiat"], 100),
    ("School Teacher — Past Paper {year}", "school-teacher", 2022, 8, ["Pakistan Studies", "General Knowledge", "English", "Computer Science", "Current Affairs"], 100),
    ("Junior Clerk — Past Paper {year}", "junior-clerk", 2024, 4, ["Pakistan Studies", "General Knowledge", "English", "Mathematics", "Computer Science", "Current Affairs"], 100),
    ("Patwari — Past Paper {year}", "patwari", 2023, 7, ["Pakistan Studies", "General Knowledge", "English", "Mathematics", "Current Affairs", "Urdu"], 100),
]


async def seed() -> None:
    """Insert sample papers with questions."""
    async with async_session() as db:
        # Pre-load job types and topics
        jt_result = await db.execute(select(JobType))
        job_types = {jt.slug: jt for jt in jt_result.scalars().all()}

        topic_result = await db.execute(select(Topic))
        topics = {t.name: t for t in topic_result.scalars().all()}

        if not job_types:
            print("❌ No job types found. Run seed_job_types first.")
            return
        if not topics:
            print("❌ No topics found. Run seed_topics first.")
            return

        papers_inserted = 0
        questions_inserted = 0

        for title_tpl, jt_slug, year, month, topic_names, total_q in PAPER_TEMPLATES:
            jt = job_types.get(jt_slug)
            if not jt:
                print(f"  ⏭  Skipping — job type '{jt_slug}' not found")
                continue

            # Check if paper already exists
            existing = await db.execute(
                select(Paper).where(
                    Paper.job_type_id == jt.id,
                    Paper.paper_year == year,
                    Paper.paper_month == month,
                )
            )
            if existing.scalar_one_or_none():
                print(f"  ⏭  {title_tpl.format(year=year)} (already exists)")
                continue

            title = title_tpl.format(year=year)
            paper = Paper(
                job_type_id=jt.id,
                paper_year=year,
                paper_month=month,
                title=title,
                source="seed",
                total_questions=total_q,
                ingestion_status="completed",
            )
            db.add(paper)
            await db.flush()  # get paper.id

            # Build question pool from available topics
            question_pool = []
            for topic_name in topic_names:
                topic = topics.get(topic_name)
                samples = SAMPLE_QUESTIONS.get(topic_name, [])
                for s in samples:
                    question_pool.append((topic, s))

            # Fill up to total_q by recycling the pool
            q_num = 0
            while q_num < total_q:
                topic, sample = question_pool[q_num % len(question_pool)]
                q_num += 1
                is_repeated = random.random() < 0.15  # 15% repeat rate
                question = Question(
                    paper_id=paper.id,
                    question_number=q_num,
                    question_text=sample["q"],
                    option_a=sample["a"],
                    option_b=sample["b"],
                    option_c=sample["c"],
                    option_d=sample["d"],
                    correct_answer=sample["ans"],
                    topic_id=topic.id if topic else None,
                    difficulty_score=round(random.uniform(0.2, 0.9), 2),
                    is_repeated=is_repeated,
                    repeat_count=random.randint(1, 4) if is_repeated else 0,
                    needs_review=False,
                    year_appeared=year,
                )
                db.add(question)
                questions_inserted += 1

            # Update topic question counts
            for topic_name in topic_names:
                topic = topics.get(topic_name)
                if topic:
                    count_result = await db.execute(
                        select(func.count(Question.id)).where(Question.topic_id == topic.id)
                    )
                    topic.total_questions = count_result.scalar() or 0

            papers_inserted += 1
            print(f"  ✅ {title} ({total_q} questions)")

        await db.commit()
        print(f"\n🌱 Seed complete: {papers_inserted} papers, {questions_inserted} questions inserted.")


def main() -> None:
    print("🌱 Seeding sample PPSC papers & questions…\n")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
