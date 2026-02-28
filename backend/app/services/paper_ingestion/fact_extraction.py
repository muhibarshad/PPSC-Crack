"""
Fact Extraction Service (GPT-4o-mini)
=======================================
Extracts the core factual statement from each MCQ.
"""

from __future__ import annotations

import json
import logging

from app.services.openai.client import OpenAIService

logger = logging.getLogger(__name__)

_FACT_SYSTEM_PROMPT = """\
You are a knowledge extractor for PPSC exam preparation.

Given a list of multiple-choice questions with their correct answers, extract the core factual statement from each one.

Rules:
- The fact should be a single, clear, declarative sentence.
- Include the correct answer within the fact.
- Remove unnecessary options/distractors — only keep the truth.
- If the question is about a definition, state the definition.
- If the question is about a date/event, state the date and event.
- Keep facts concise (under 50 words each).

Return ONLY a JSON array (no markdown, no explanation):
[
  {"question_number": 1, "fact": "The capital of Pakistan is Islamabad."},
  {"question_number": 2, "fact": "The Lahore Resolution was passed in 1940."},
  ...
]
"""


async def extract_facts(
    openai_svc: OpenAIService,
    questions: list[dict],
    *,
    batch_size: int = 25,
) -> dict[int, str]:
    """Extract core facts from questions using GPT-4o-mini.

    Parameters
    ----------
    openai_svc:
        The centralized OpenAI service.
    questions:
        List of dicts with ``question_number``, ``question_text``,
        ``option_a``..``option_d``, ``correct_answer``.
    batch_size:
        Process in batches to avoid context-window overflow.

    Returns
    -------
    dict[int, str]
        ``{question_number: extracted_fact}``
    """
    all_facts: dict[int, str] = {}

    for i in range(0, len(questions), batch_size):
        batch = questions[i : i + batch_size]
        batch_data = [
            {
                "question_number": q["question_number"],
                "question_text": q["question_text"],
                "options": {
                    "A": q.get("option_a", ""),
                    "B": q.get("option_b", ""),
                    "C": q.get("option_c", ""),
                    "D": q.get("option_d", ""),
                },
                "correct_answer": q.get("correct_answer", "unknown"),
            }
            for q in batch
        ]

        user_prompt = json.dumps(batch_data, ensure_ascii=False)

        raw = await openai_svc.classify(  # uses GPT-4o-mini
            system_prompt=_FACT_SYSTEM_PROMPT,
            text=user_prompt,
            response_format={"type": "json_object"},
        )

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                facts_list = parsed.get("facts", parsed.get("results", []))
            elif isinstance(parsed, list):
                facts_list = parsed
            else:
                facts_list = []
        except json.JSONDecodeError:
            logger.error("Fact extraction returned invalid JSON (batch %d): %s", i, raw[:500])
            facts_list = []

        for item in facts_list:
            q_num = item.get("question_number")
            fact = item.get("fact", "")
            if q_num is not None and fact:
                all_facts[q_num] = fact

    logger.info("Extracted facts for %d/%d questions", len(all_facts), len(questions))
    return all_facts
