"""
Current Affairs MCQ Generator
================================
Uses GPT-4o to produce exam-style MCQs from top daily current affairs.
Output format matches PPSC past-paper MCQ structure.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.models.current_affair import CurrentAffairsItem
from app.services.openai.client import OpenAIService, get_openai_service
from app.services.openai.models import OpenAICallType

logger = logging.getLogger(__name__)

MCQ_SYSTEM_PROMPT = """You are an expert PPSC (Punjab Public Service Commission) exam question setter 
specialising in Current Affairs. Your task is to generate a single high-quality MCQ from the given 
news article that tests factual recall in the style of a PPSC competitive exam.

RULES:
1. The question must be factual and directly based on the article content.
2. There must be exactly 4 options (a, b, c, d).
3. Only one option is correct.
4. Distractors must be plausible but clearly wrong.
5. The question should be self-contained — a student should be able to answer it 
   without having read the article.
6. Provide a brief 1-2 sentence explanation for the correct answer.
7. Match the difficulty level of typical PPSC general knowledge questions.

Return ONLY valid JSON (no markdown, no code fences) in this exact format:
{
  "question": "The actual MCQ question text?",
  "options": {
    "a": "First option",
    "b": "Second option",
    "c": "Third option",
    "d": "Fourth option"
  },
  "correct_answer": "a",
  "explanation": "Brief explanation of why this is correct."
}"""


MCQ_USER_TEMPLATE = """Generate a PPSC-style MCQ from this current affairs article.

Category: {category}
Headline: {headline}
Published: {published_date}

Article Content:
{content}"""


async def generate_mcq_for_article(
    article: CurrentAffairsItem,
    openai_svc: OpenAIService | None = None,
) -> dict[str, Any] | None:
    """Generate a single MCQ for a current affairs article using GPT-4o.

    Returns a dict with keys: question, options, correct_answer, explanation
    or None if generation fails.
    """
    svc = openai_svc or get_openai_service()

    user_prompt = MCQ_USER_TEMPLATE.format(
        category=article.category,
        headline=article.headline,
        published_date=article.published_date or "Unknown",
        content=(article.content or article.summary or "")[:4000],
    )

    try:
        raw_response = await svc.chat(
            messages=[
                {"role": "system", "content": MCQ_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            call_type=OpenAICallType.PAPER_PROCESSING,
            model="gpt-4o",
            temperature=0.3,
            max_tokens=800,
            response_format={"type": "json_object"},
        )

        mcq_data = json.loads(raw_response)

        # Validate structure
        required_keys = {"question", "options", "correct_answer", "explanation"}
        if not required_keys.issubset(mcq_data.keys()):
            logger.warning(
                "MCQ generation returned incomplete JSON for article %s: %s",
                article.id, mcq_data.keys(),
            )
            return None

        options = mcq_data["options"]
        if not isinstance(options, dict) or set(options.keys()) != {"a", "b", "c", "d"}:
            logger.warning("MCQ options malformed for article %s", article.id)
            return None

        correct = mcq_data["correct_answer"].lower().strip()
        if correct not in ("a", "b", "c", "d"):
            logger.warning("MCQ correct_answer invalid for article %s: %s", article.id, correct)
            return None

        return {
            "mcq_text": mcq_data["question"],
            "mcq_options": options,
            "mcq_correct_answer": correct,
            "mcq_explanation": mcq_data["explanation"],
        }

    except json.JSONDecodeError as exc:
        logger.error("Failed to parse MCQ JSON for article %s: %s", article.id, exc)
    except Exception as exc:
        logger.exception("MCQ generation failed for article %s: %s", article.id, exc)

    return None


async def generate_mcqs_for_top_articles(
    articles: list[CurrentAffairsItem],
    *,
    max_count: int = 10,
    openai_svc: OpenAIService | None = None,
) -> list[tuple[CurrentAffairsItem, dict[str, Any]]]:
    """Generate MCQs for the top N articles (by relevance_score).

    Returns a list of (article, mcq_data) tuples for successful generations.
    """
    svc = openai_svc or get_openai_service()

    # Sort by relevance and take top N that don't already have MCQs
    candidates = sorted(
        [a for a in articles if not a.mcq_generated],
        key=lambda a: a.relevance_score,
        reverse=True,
    )[:max_count]

    results: list[tuple[CurrentAffairsItem, dict[str, Any]]] = []

    for article in candidates:
        mcq_data = await generate_mcq_for_article(article, openai_svc=svc)
        if mcq_data:
            results.append((article, mcq_data))
            logger.info("Generated MCQ for article %s: %s", article.id, article.headline[:60])
        else:
            logger.warning("Skipped MCQ generation for article %s", article.id)

    logger.info("Generated %d MCQs out of %d candidates", len(results), len(candidates))
    return results
