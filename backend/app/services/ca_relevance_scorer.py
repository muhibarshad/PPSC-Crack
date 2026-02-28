"""
Current Affairs Relevance Scorer
==================================
Computes a composite relevance score for each RSS article to decide
whether it's exam-worthy for PPSC candidates.

Score = w1·keyword + w2·semantic + w3·recency + w4·category

Components:
  1. **Keyword score** — match against learned CA patterns from past papers.
  2. **Semantic score** — pgvector cosine similarity to historical CA questions.
  3. **Recency score** — exponential decay favouring recent articles.
  4. **Category score** — boost if the article's category matches the learned
     category frequency profile from ingested papers.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Sequence

from sqlalchemy import select, func, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.models.current_affair import CurrentAffairsItem
from app.services.rss_fetcher import RawArticle
from app.services.openai.client import get_openai_service

logger = logging.getLogger(__name__)

# ── Score weights (tuned for PPSC CA questions) ──────────────
W_KEYWORD = 0.30
W_SEMANTIC = 0.35
W_RECENCY = 0.15
W_CATEGORY = 0.20

# ── Relevance threshold ─────────────────────────────────────
RELEVANCE_THRESHOLD = 0.65

# ── Valid CA categories ──────────────────────────────────────
CA_CATEGORIES = [
    "govt_appointment",
    "sports",
    "science",
    "economy",
    "international",
    "records",
]

# ── Keyword banks — learned from typical PPSC CA patterns ────
# These are seeded and can later be enriched by analysing ingested papers.
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "govt_appointment": [
        "appointed", "appointment", "posting", "transfer", "chief secretary",
        "governor", "minister", "secretary", "commissioner", "dg", "director general",
        "chief justice", "judge", "chairman", "ambassador", "high commissioner",
        "caretaker", "cm", "pm", "president", "federal", "provincial",
        "sworn in", "assumed charge", "took oath",
    ],
    "sports": [
        "cricket", "hockey", "football", "kabaddi", "olympic", "medal",
        "world cup", "t20", "psl", "pct", "champion", "tournament",
        "record", "player", "captain", "team", "match", "final",
        "trophy", "icc", "fifa", "pcb", "asian games", "commonwealth",
    ],
    "science": [
        "satellite", "nasa", "space", "isro", "suparco", "launch",
        "discovery", "scientist", "research", "technology", "invention",
        "ai", "artificial intelligence", "nuclear", "quantum", "vaccine",
        "mars", "moon", "planet", "climate", "species", "dna", "gene",
    ],
    "economy": [
        "gdp", "inflation", "budget", "imf", "world bank", "sbp",
        "interest rate", "forex", "exports", "imports", "trade",
        "revenue", "tax", "stock", "investment", "rupee", "dollar",
        "debt", "deficit", "growth rate", "cpec", "fdi", "remittances",
    ],
    "international": [
        "united nations", "un", "g7", "g20", "nato", "eu", "brics",
        "summit", "bilateral", "treaty", "agreement", "sanctions",
        "diplomat", "foreign minister", "embassy", "resolution",
        "oic", "saarc", "sco", "asean", "peace", "conflict", "war",
    ],
    "records": [
        "record", "highest", "lowest", "first", "largest", "longest",
        "youngest", "oldest", "fastest", "guinness", "milestone",
        "unprecedented", "historic", "new record", "broke record",
        "world record", "national record",
    ],
}

# Flatten for general keyword matching
ALL_KEYWORDS: set[str] = set()
for kws in CATEGORY_KEYWORDS.values():
    ALL_KEYWORDS.update(kws)


@dataclass
class RelevanceResult:
    """Breakdown of the relevance scoring for an article."""

    keyword_score: float = 0.0
    semantic_score: float = 0.0
    recency_score: float = 0.0
    category_score: float = 0.0
    composite_score: float = 0.0
    matched_category: str = "international"  # default fallback
    matched_keywords: list[str] | None = None


# ═══════════════════════════════════════════════════════════
# 1. Keyword Score
# ═══════════════════════════════════════════════════════════

def compute_keyword_score(article: RawArticle) -> tuple[float, str, list[str]]:
    """Match article text against the keyword bank.

    Returns (score 0-1, best_category, matched_keywords).
    """
    combined_text = f"{article.headline} {article.summary} {article.content}".lower()
    best_category = "international"
    best_count = 0
    matched: list[str] = []

    for category, keywords in CATEGORY_KEYWORDS.items():
        cat_matches = [kw for kw in keywords if kw in combined_text]
        if len(cat_matches) > best_count:
            best_count = len(cat_matches)
            best_category = category
            matched = cat_matches

    # Normalise: 5+ keyword hits = 1.0
    score = min(best_count / 5.0, 1.0)
    return score, best_category, matched


# ═══════════════════════════════════════════════════════════
# 2. Semantic Score (pgvector cosine similarity)
# ═══════════════════════════════════════════════════════════

async def compute_semantic_score(
    db: AsyncSession,
    article_embedding: list[float],
    *,
    top_k: int = 5,
) -> float:
    """Cosine similarity against historical CA questions with embeddings.

    Returns average similarity of top-k matches (0-1).
    """
    if not article_embedding:
        return 0.0

    vec_literal = f"[{','.join(str(v) for v in article_embedding)}]"

    # Search against questions that are CA-related (topic-based or keyword heuristic)
    stmt = sa_text(f"""
        SELECT 1 - (embedding <=> '{vec_literal}'::vector) AS similarity
        FROM questions
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> '{vec_literal}'::vector
        LIMIT :top_k
    """)

    result = await db.execute(stmt, {"top_k": top_k})
    rows = result.fetchall()

    if not rows:
        return 0.0

    similarities = [float(row[0]) for row in rows if float(row[0]) > 0]
    if not similarities:
        return 0.0

    return sum(similarities) / len(similarities)


# ═══════════════════════════════════════════════════════════
# 3. Recency Score
# ═══════════════════════════════════════════════════════════

def compute_recency_score(published_date: date | None) -> float:
    """Exponential decay: today=1.0, 7 days ago=0.5, 30+ days=~0.

    Uses half-life of 7 days.
    """
    if published_date is None:
        return 0.5  # Unknown date gets a neutral score

    today = date.today()
    days_old = max((today - published_date).days, 0)

    half_life = 7.0
    return math.exp(-0.693 * days_old / half_life)  # ln(2) ≈ 0.693


# ═══════════════════════════════════════════════════════════
# 4. Category Score
# ═══════════════════════════════════════════════════════════

async def build_category_frequency_profile(db: AsyncSession) -> dict[str, float]:
    """Analyse all questions from ingested papers to determine
    how frequently each CA category appears.

    Returns a dict mapping category → normalised frequency (0-1).
    """
    # Count questions per topic that map to CA categories
    profile: dict[str, float] = {cat: 0.0 for cat in CA_CATEGORIES}

    # Heuristic: count questions whose text matches CA category keywords
    for category, keywords in CATEGORY_KEYWORDS.items():
        conditions = " OR ".join(
            [f"LOWER(question_text) LIKE '%{kw}%'" for kw in keywords[:8]]
        )
        stmt = sa_text(f"""
            SELECT COUNT(*) FROM questions
            WHERE ({conditions})
        """)
        result = await db.execute(stmt)
        count = result.scalar() or 0
        profile[category] = float(count)

    total = sum(profile.values())
    if total > 0:
        for cat in profile:
            profile[cat] /= total
    else:
        # Uniform distribution fallback
        uniform = 1.0 / len(CA_CATEGORIES)
        profile = {cat: uniform for cat in CA_CATEGORIES}

    return profile


def compute_category_score(
    matched_category: str,
    category_profile: dict[str, float],
) -> float:
    """How well does the article's category align with historical patterns.

    Higher frequency in past papers = higher score.
    """
    raw = category_profile.get(matched_category, 0.0)
    # Scale: the most frequent category gets 1.0
    max_freq = max(category_profile.values()) if category_profile else 1.0
    if max_freq == 0:
        return 0.5
    return min(raw / max_freq, 1.0)


# ═══════════════════════════════════════════════════════════
# Composite Scorer
# ═══════════════════════════════════════════════════════════

async def score_article(
    db: AsyncSession,
    article: RawArticle,
    category_profile: dict[str, float],
    article_embedding: list[float] | None = None,
) -> RelevanceResult:
    """Compute the full composite relevance score for an article."""

    # 1. Keyword
    kw_score, matched_cat, matched_kws = compute_keyword_score(article)

    # Use RSS category tags as a hint
    if article.raw_categories:
        for rss_cat in article.raw_categories:
            for ca_cat in CA_CATEGORIES:
                if ca_cat.replace("_", " ") in rss_cat or rss_cat in ca_cat:
                    matched_cat = ca_cat
                    break

    # 2. Semantic
    sem_score = 0.0
    if article_embedding:
        sem_score = await compute_semantic_score(db, article_embedding)

    # 3. Recency
    rec_score = compute_recency_score(article.published_date)

    # 4. Category
    cat_score = compute_category_score(matched_cat, category_profile)

    # Composite
    composite = (
        W_KEYWORD * kw_score
        + W_SEMANTIC * sem_score
        + W_RECENCY * rec_score
        + W_CATEGORY * cat_score
    )

    return RelevanceResult(
        keyword_score=round(kw_score, 4),
        semantic_score=round(sem_score, 4),
        recency_score=round(rec_score, 4),
        category_score=round(cat_score, 4),
        composite_score=round(composite, 4),
        matched_category=matched_cat,
        matched_keywords=matched_kws,
    )
