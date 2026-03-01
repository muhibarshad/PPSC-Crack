"""
Seed Script — Insert sample current affairs items for demo.
================================================================
Run:  python -m app.scripts.seed_current_affairs

Creates realistic current affairs items with MCQs, relevance scores,
and approval statuses to populate the Current Affairs dashboard.
"""

import asyncio
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.database import async_session
from app.models.current_affair import CurrentAffairsItem
from sqlalchemy import select


SEED_CURRENT_AFFAIRS = [
    {
        "headline": "Pakistan Successfully Launches Satellite iCube-Qamar II",
        "summary": "Pakistan's second lunar satellite iCube-Qamar II has been successfully launched, marking another milestone in the country's space program.",
        "content": "Pakistan's Institute of Space Technology (IST) in collaboration with SUPARCO has successfully launched iCube-Qamar II, the country's second lunar orbiter satellite. The satellite was launched aboard a Chinese Long March 5 rocket. It carries advanced imaging equipment and will study the lunar surface for potential resources. The mission strengthens Pakistan's growing presence in space exploration and opens new avenues for scientific research.",
        "category": "Science & Technology",
        "source_name": "dawn",
        "source_url": "https://dawn.com/news/sample-icube-qamar-2",
        "published_date": "2026-01-15",
        "relevance_score": 0.92,
        "keyword_score": 0.85,
        "semantic_score": 0.90,
        "recency_score": 0.95,
        "category_score": 0.88,
        "mcq_generated": True,
        "mcq_text": "Pakistan's second lunar satellite launched in 2026 is called:",
        "mcq_options": {"a": "iCube-Qamar", "b": "iCube-Qamar II", "c": "PakSat-II", "d": "BadrSat-2"},
        "mcq_correct_answer": "b",
        "mcq_explanation": "iCube-Qamar II is Pakistan's second lunar satellite, a follow-up to the original iCube-Qamar mission.",
        "is_approved": True,
        "is_included_in_prediction": True,
    },
    {
        "headline": "PM Announces Rs 200 Billion IT Export Package",
        "summary": "Prime Minister announces a comprehensive Rs 200 billion package to boost IT exports and create 500,000 new jobs in the technology sector.",
        "content": "The Prime Minister of Pakistan has announced a comprehensive Rs 200 billion package aimed at boosting IT exports to $10 billion by 2028. The package includes tax incentives for IT companies, establishment of 50 new tech parks across Pakistan, subsidized internet for freelancers, and scholarship programs for AI and cybersecurity education. Pakistan's IT exports currently stand at $3.2 billion, and the government aims to triple this figure through strategic investments.",
        "category": "Economy",
        "source_name": "geo",
        "source_url": "https://geo.tv/news/sample-it-package",
        "published_date": "2026-01-20",
        "relevance_score": 0.88,
        "keyword_score": 0.82,
        "semantic_score": 0.86,
        "recency_score": 0.92,
        "category_score": 0.90,
        "mcq_generated": True,
        "mcq_text": "The government's IT export target by 2028 is:",
        "mcq_options": {"a": "$5 billion", "b": "$8 billion", "c": "$10 billion", "d": "$15 billion"},
        "mcq_correct_answer": "c",
        "mcq_explanation": "The PM's IT export package targets $10 billion in IT exports by 2028.",
        "is_approved": True,
        "is_included_in_prediction": True,
    },
    {
        "headline": "Punjab Introduces Digital Land Records System Province-wide",
        "summary": "Punjab government rolls out a fully digital land records system across all 36 districts to reduce corruption and streamline revenue administration.",
        "content": "The Punjab government has completed the province-wide rollout of its digital land records system, covering all 36 districts. The system allows citizens to access land records online, apply for mutations digitally, and track their applications in real-time. The initiative has reduced average mutation processing time from 45 days to just 7 days. Over 50 million land record entries have been digitized. The system also includes satellite imagery integration for dispute resolution.",
        "category": "Governance",
        "source_name": "dawn",
        "source_url": "https://dawn.com/news/sample-digital-land-records",
        "published_date": "2026-02-01",
        "relevance_score": 0.95,
        "keyword_score": 0.90,
        "semantic_score": 0.88,
        "recency_score": 0.98,
        "category_score": 0.95,
        "mcq_generated": True,
        "mcq_text": "Punjab's digital land records system covers how many districts?",
        "mcq_options": {"a": "24", "b": "30", "c": "36", "d": "40"},
        "mcq_correct_answer": "c",
        "mcq_explanation": "Punjab has 36 districts, all now covered by the digital land records system.",
        "is_approved": True,
        "is_included_in_prediction": True,
    },
    {
        "headline": "CPEC Phase-III Focuses on Agricultural Modernization",
        "summary": "CPEC's third phase priorities include agricultural modernization, tech transfer, and climate-resilient farming techniques.",
        "content": "The third phase of the China-Pakistan Economic Corridor (CPEC) will focus on agricultural modernization, technology transfer, and rural development. Key projects include establishing 10 model farms using Chinese agricultural technology, a $500 million water conservation initiative in Sindh and Balochistan, and training 100,000 farmers in climate-resilient farming techniques. Both countries signed 12 MoUs during the recent visit of the Chinese Vice Premier.",
        "category": "International Relations",
        "source_name": "app",
        "source_url": "https://app.com.pk/news/sample-cpec-phase-3",
        "published_date": "2026-02-05",
        "relevance_score": 0.90,
        "keyword_score": 0.88,
        "semantic_score": 0.85,
        "recency_score": 0.95,
        "category_score": 0.92,
        "mcq_generated": True,
        "mcq_text": "CPEC Phase-III primarily focuses on:",
        "mcq_options": {"a": "Energy projects", "b": "Road infrastructure", "c": "Agricultural modernization", "d": "Defense cooperation"},
        "mcq_correct_answer": "c",
        "mcq_explanation": "CPEC Phase-III prioritizes agricultural modernization and rural development.",
        "is_approved": True,
        "is_included_in_prediction": True,
    },
    {
        "headline": "Supreme Court Landmark Ruling on Right to Information",
        "summary": "The Supreme Court of Pakistan rules that the right to information is a fundamental right under Article 19-A of the Constitution.",
        "content": "In a landmark judgment, the Supreme Court of Pakistan has reaffirmed that the Right to Information is a fundamental right guaranteed under Article 19-A of the Constitution. The court directed all federal and provincial government bodies to proactively disclose information of public interest within 90 days. The ruling strengthens the legal framework for transparency and accountability in governance.",
        "category": "Law & Judiciary",
        "source_name": "dawn",
        "source_url": "https://dawn.com/news/sample-rti-ruling",
        "published_date": "2026-02-10",
        "relevance_score": 0.87,
        "keyword_score": 0.82,
        "semantic_score": 0.84,
        "recency_score": 0.90,
        "category_score": 0.92,
        "mcq_generated": True,
        "mcq_text": "Right to Information in Pakistan's Constitution is guaranteed under:",
        "mcq_options": {"a": "Article 14", "b": "Article 19", "c": "Article 19-A", "d": "Article 25"},
        "mcq_correct_answer": "c",
        "mcq_explanation": "Article 19-A of the 1973 Constitution guarantees the right to access information.",
        "is_approved": True,
        "is_included_in_prediction": True,
    },
    {
        "headline": "Pakistan Achieves 50% Renewable Energy Milestone",
        "summary": "Pakistan has achieved 50% electricity generation from renewable sources including solar, wind, and hydel power.",
        "content": "Pakistan has achieved a historic milestone by generating 50% of its total electricity from renewable sources. The achievement comes after rapid expansion of solar and wind farms in Sindh and Balochistan, along with the completion of the Dasu Hydropower Project. The government's Renewable Energy Policy 2025 set this target, which has been achieved ahead of schedule. Pakistan's total installed renewable capacity now stands at 25,000 MW.",
        "category": "Energy & Environment",
        "source_name": "geo",
        "source_url": "https://geo.tv/news/sample-renewable-energy",
        "published_date": "2026-02-15",
        "relevance_score": 0.86,
        "keyword_score": 0.80,
        "semantic_score": 0.82,
        "recency_score": 0.92,
        "category_score": 0.88,
        "mcq_generated": True,
        "mcq_text": "Pakistan's renewable energy generation milestone in 2026 reached:",
        "mcq_options": {"a": "30%", "b": "40%", "c": "50%", "d": "60%"},
        "mcq_correct_answer": "c",
        "mcq_explanation": "Pakistan achieved 50% electricity generation from renewables in 2026.",
        "is_approved": True,
        "is_included_in_prediction": False,
    },
    {
        "headline": "New National Education Policy 2026 Announced",
        "summary": "Federal Education Ministry announces NEP 2026 focusing on digital literacy, STEM education, and teacher training reforms.",
        "content": "The Federal Ministry of Education has unveiled the National Education Policy 2026, focusing on digital literacy integration from primary level, mandatory STEM education in secondary schools, comprehensive teacher training reforms, and establishment of 200 smart schools across Pakistan. The policy also introduces a national learning assessment framework aligned with international standards.",
        "category": "Education",
        "source_name": "app",
        "source_url": "https://app.com.pk/news/sample-nep-2026",
        "published_date": "2026-01-25",
        "relevance_score": 0.93,
        "keyword_score": 0.90,
        "semantic_score": 0.88,
        "recency_score": 0.94,
        "category_score": 0.95,
        "mcq_generated": True,
        "mcq_text": "National Education Policy 2026 mandates ___ education in secondary schools:",
        "mcq_options": {"a": "Religious", "b": "STEM", "c": "Vocational", "d": "Physical"},
        "mcq_correct_answer": "b",
        "mcq_explanation": "NEP 2026 makes STEM education mandatory in secondary schools.",
        "is_approved": True,
        "is_included_in_prediction": True,
    },
    {
        "headline": "Pakistan-Saudi Arabia Sign $5 Billion Investment Deal",
        "summary": "Pakistan and Saudi Arabia sign agreements worth $5 billion covering mining, agriculture, IT, and infrastructure sectors.",
        "content": "Pakistan and Saudi Arabia have signed a landmark $5 billion investment agreement during the Saudi Crown Prince's visit to Islamabad. The deal covers investments in Reko Diq mining project, agricultural zones in Sindh and Punjab, IT parks in Islamabad and Lahore, and infrastructure development in Gwadar. This is the largest single investment commitment from Saudi Arabia to Pakistan.",
        "category": "International Relations",
        "source_name": "dawn",
        "source_url": "https://dawn.com/news/sample-saudi-deal",
        "published_date": "2026-02-20",
        "relevance_score": 0.91,
        "keyword_score": 0.86,
        "semantic_score": 0.88,
        "recency_score": 0.96,
        "category_score": 0.90,
        "mcq_generated": True,
        "mcq_text": "The Pakistan-Saudi Arabia investment deal signed in 2026 is worth:",
        "mcq_options": {"a": "$2 billion", "b": "$3 billion", "c": "$5 billion", "d": "$8 billion"},
        "mcq_correct_answer": "c",
        "mcq_explanation": "Pakistan and Saudi Arabia signed a $5 billion investment agreement in 2026.",
        "is_approved": True,
        "is_included_in_prediction": True,
    },
    {
        "headline": "Census 2026: Pakistan Population Reaches 250 Million",
        "summary": "Pakistan's 7th digital census reveals population of 250 million with 38% urbanization rate.",
        "content": "The preliminary results of Pakistan's 7th population census, conducted digitally for the first time, show the country's population has reached 250 million. Punjab remains the most populous province with 120 million people. The urbanization rate has increased to 38%. The census data will be crucial for resource allocation, constituency delimitation, and development planning.",
        "category": "Demographics",
        "source_name": "geo",
        "source_url": "https://geo.tv/news/sample-census-2026",
        "published_date": "2026-02-25",
        "relevance_score": 0.94,
        "keyword_score": 0.92,
        "semantic_score": 0.90,
        "recency_score": 0.97,
        "category_score": 0.93,
        "mcq_generated": True,
        "mcq_text": "According to Census 2026, Pakistan's population is approximately:",
        "mcq_options": {"a": "200 million", "b": "220 million", "c": "250 million", "d": "280 million"},
        "mcq_correct_answer": "c",
        "mcq_explanation": "Census 2026 data shows Pakistan's population at approximately 250 million.",
        "is_approved": True,
        "is_included_in_prediction": True,
    },
    {
        "headline": "SBP Reduces Policy Rate to 10% Amid Inflation Decline",
        "summary": "State Bank of Pakistan cuts policy rate by 100 basis points to 10% as inflation drops below 8%.",
        "content": "The State Bank of Pakistan's Monetary Policy Committee has decided to reduce the policy rate by 100 basis points to 10%, citing declining inflation which has fallen to 7.8% year-on-year. This is the fifth consecutive rate cut since June 2024. The SBP expects further economic stabilization with GDP growth projected at 3.5% for FY2025-26. Credit growth has increased by 15% following the monetary easing cycle.",
        "category": "Economy",
        "source_name": "dawn",
        "source_url": "https://dawn.com/news/sample-sbp-rate-cut",
        "published_date": "2026-01-28",
        "relevance_score": 0.89,
        "keyword_score": 0.85,
        "semantic_score": 0.87,
        "recency_score": 0.93,
        "category_score": 0.91,
        "mcq_generated": True,
        "mcq_text": "SBP's policy rate in early 2026 was reduced to:",
        "mcq_options": {"a": "8%", "b": "10%", "c": "12%", "d": "15%"},
        "mcq_correct_answer": "b",
        "mcq_explanation": "The State Bank reduced the policy rate to 10% in January 2026.",
        "is_approved": True,
        "is_included_in_prediction": True,
    },
]


async def seed() -> None:
    """Insert sample current affairs items."""
    async with async_session() as db:
        inserted = 0
        skipped = 0

        for item_data in SEED_CURRENT_AFFAIRS:
            # Check by unique source_url
            existing = await db.execute(
                select(CurrentAffairsItem).where(
                    CurrentAffairsItem.source_url == item_data["source_url"]
                )
            )
            if existing.scalar_one_or_none():
                print(f"  ⏭  {item_data['headline'][:50]}… (already exists)")
                skipped += 1
                continue

            # Convert date string
            data = {**item_data}
            data["published_date"] = date.fromisoformat(data["published_date"])
            if data.get("is_approved"):
                data["approved_at"] = datetime.now(timezone.utc)

            obj = CurrentAffairsItem(**data)
            db.add(obj)
            print(f"  ✅ {item_data['headline'][:60]}")
            inserted += 1

        await db.commit()
        print(f"\n🌱 Current affairs seed: {inserted} inserted, {skipped} skipped.")


def main() -> None:
    print("🌱 Seeding Current Affairs…\n")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
