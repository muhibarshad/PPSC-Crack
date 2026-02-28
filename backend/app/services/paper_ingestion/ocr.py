"""
GPT-4o Vision OCR Service
===========================
Extracts structured MCQ data from scanned exam paper images using
GPT-4o Vision.  Returns structured JSON with per-question confidence
scores.

Two-phase extraction:
1. **Questions image** → numbered MCQs with A/B/C/D options + confidence
2. **Answer key image** → question_number → correct_answer mapping
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from app.services.openai.client import OpenAIService
from app.services.openai.models import OpenAICallType

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════

@dataclass
class OCRQuestion:
    """A single MCQ extracted via Vision OCR."""
    question_number: int
    question_text: str
    option_a: str | None = None
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None
    confidence: float = 0.0  # 0.0 - 1.0


@dataclass
class OCRAnswerMapping:
    """Answer key entry extracted via Vision OCR."""
    question_number: int
    correct_answer: str  # a/b/c/d
    confidence: float = 0.0


@dataclass
class OCRResult:
    """Full OCR extraction result."""
    questions: list[OCRQuestion] = field(default_factory=list)
    answers: list[OCRAnswerMapping] = field(default_factory=list)
    questions_raw_text: str = ""
    answers_raw_text: str = ""
    warnings: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════
# Prompts
# ═══════════════════════════════════════════════════════════

QUESTIONS_EXTRACTION_PROMPT = """You are an expert OCR system specialized in extracting Multiple Choice Questions (MCQs) from scanned Pakistani exam papers (PPSC/FPSC/CSS).

Analyze this scanned image and extract ALL numbered MCQ questions with their options (A, B, C, D).

Return a JSON object with this EXACT structure:
{
  "questions": [
    {
      "question_number": 1,
      "question_text": "The full question text exactly as written",
      "option_a": "First option text",
      "option_b": "Second option text",
      "option_c": "Third option text",
      "option_d": "Fourth option text",
      "confidence": 0.95
    }
  ],
  "total_detected": 100,
  "warnings": ["Any issues like blurry areas, cut-off text, etc."]
}

RULES:
- Extract EVERY question visible in the image.
- Preserve original text exactly (do NOT correct spelling/grammar).
- The `confidence` score (0.0 to 1.0) should reflect how clearly you can read the text:
  - 0.95-1.0: Crystal clear, no ambiguity
  - 0.85-0.94: Readable but minor uncertainty (slight blur, small print)
  - 0.70-0.84: Partially unclear, some characters uncertain
  - Below 0.70: Significant portions unreadable
- If an option is missing or unreadable, set it to null.
- If question text is partially cut off, extract what's visible and set low confidence.
- Return ONLY the JSON, no other text."""

ANSWER_KEY_EXTRACTION_PROMPT = """You are an expert OCR system specialized in extracting answer keys from scanned Pakistani exam papers (PPSC/FPSC/CSS).

Analyze this scanned answer key image and extract the mapping of question numbers to correct answers.

Return a JSON object with this EXACT structure:
{
  "answers": [
    {
      "question_number": 1,
      "correct_answer": "c",
      "confidence": 0.98
    }
  ],
  "total_detected": 100,
  "warnings": ["Any issues like unclear markings, etc."]
}

RULES:
- Extract ALL answer mappings visible in the image.
- correct_answer must be lowercase: a, b, c, or d.
- The `confidence` score (0.0 to 1.0) reflects readability:
  - 0.95-1.0: Clear and unambiguous
  - 0.85-0.94: Readable but slightly uncertain
  - Below 0.85: Uncertain or ambiguous
- Common formats: "1-C", "1. C", "1=C", bubbled answer sheets, etc.
- Return ONLY the JSON, no other text."""


# ═══════════════════════════════════════════════════════════
# OCR Functions
# ═══════════════════════════════════════════════════════════

async def extract_questions_from_image(
    openai: OpenAIService,
    image_source: str | bytes,
    *,
    additional_context: str = "",
) -> list[OCRQuestion]:
    """Send a questions image to GPT-4o Vision and extract structured MCQs.

    Parameters
    ----------
    openai:
        The OpenAI service instance.
    image_source:
        Image URL (S3/R2) or raw bytes.
    additional_context:
        Extra instructions (e.g., "This is page 2 of the questions").

    Returns
    -------
    list[OCRQuestion]
        Extracted questions with confidence scores.
    """
    prompt = QUESTIONS_EXTRACTION_PROMPT
    if additional_context:
        prompt += f"\n\nAdditional context: {additional_context}"

    logger.info("Running Vision OCR on questions image...")
    raw_response = await openai.vision_ocr(
        image_source=image_source,
        prompt=prompt,
        temperature=0.1,
        max_tokens=8192,
    )

    questions = _parse_questions_response(raw_response)
    logger.info("Vision OCR extracted %d questions", len(questions))
    return questions


async def extract_answers_from_image(
    openai: OpenAIService,
    image_source: str | bytes,
    *,
    additional_context: str = "",
) -> list[OCRAnswerMapping]:
    """Send an answer key image to GPT-4o Vision and extract mappings.

    Parameters
    ----------
    openai:
        The OpenAI service instance.
    image_source:
        Image URL (S3/R2) or raw bytes.

    Returns
    -------
    list[OCRAnswerMapping]
        Extracted answer mappings with confidence scores.
    """
    prompt = ANSWER_KEY_EXTRACTION_PROMPT
    if additional_context:
        prompt += f"\n\nAdditional context: {additional_context}"

    logger.info("Running Vision OCR on answer key image...")
    raw_response = await openai.vision_ocr(
        image_source=image_source,
        prompt=prompt,
        temperature=0.1,
        max_tokens=4096,
    )

    answers = _parse_answers_response(raw_response)
    logger.info("Vision OCR extracted %d answer mappings", len(answers))
    return answers


async def run_full_ocr(
    openai: OpenAIService,
    question_images: list[str | bytes],
    answer_images: list[str | bytes],
) -> OCRResult:
    """Run the full 2-phase OCR pipeline on multiple images.

    Parameters
    ----------
    openai:
        OpenAI service instance.
    question_images:
        List of image URLs or bytes for question pages.
    answer_images:
        List of image URLs or bytes for answer key pages.

    Returns
    -------
    OCRResult
        Combined extraction result.
    """
    result = OCRResult()

    # Phase 1: Extract questions from all question images
    all_questions: list[OCRQuestion] = []
    for i, img in enumerate(question_images):
        context = f"Page {i + 1} of {len(question_images)} question pages." if len(question_images) > 1 else ""
        try:
            qs = await extract_questions_from_image(openai, img, additional_context=context)
            all_questions.extend(qs)
        except Exception as exc:
            logger.warning("Failed to OCR question image %d: %s", i + 1, exc)
            result.warnings.append(f"Failed to process question image {i + 1}: {exc}")

    # Deduplicate by question number (keep highest confidence)
    q_map: dict[int, OCRQuestion] = {}
    for q in all_questions:
        if q.question_number not in q_map or q.confidence > q_map[q.question_number].confidence:
            q_map[q.question_number] = q
    result.questions = sorted(q_map.values(), key=lambda x: x.question_number)

    # Phase 2: Extract answers from all answer images
    all_answers: list[OCRAnswerMapping] = []
    for i, img in enumerate(answer_images):
        context = f"Page {i + 1} of {len(answer_images)} answer key pages." if len(answer_images) > 1 else ""
        try:
            ans = await extract_answers_from_image(openai, img, additional_context=context)
            all_answers.extend(ans)
        except Exception as exc:
            logger.warning("Failed to OCR answer image %d: %s", i + 1, exc)
            result.warnings.append(f"Failed to process answer image {i + 1}: {exc}")

    # Deduplicate answers by question number (keep highest confidence)
    a_map: dict[int, OCRAnswerMapping] = {}
    for a in all_answers:
        if a.question_number not in a_map or a.confidence > a_map[a.question_number].confidence:
            a_map[a.question_number] = a
    result.answers = sorted(a_map.values(), key=lambda x: x.question_number)

    logger.info(
        "Full OCR complete: %d questions, %d answers extracted",
        len(result.questions), len(result.answers),
    )
    return result


# ═══════════════════════════════════════════════════════════
# Response Parsers
# ═══════════════════════════════════════════════════════════

def _parse_questions_response(raw: str) -> list[OCRQuestion]:
    """Parse GPT-4o Vision response into OCRQuestion objects."""
    try:
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            # Remove language identifier like "json"
            if text.startswith("json"):
                text = text[4:].strip()

        data = json.loads(text)
        questions: list[OCRQuestion] = []

        for item in data.get("questions", []):
            try:
                q = OCRQuestion(
                    question_number=int(item["question_number"]),
                    question_text=str(item.get("question_text", "")).strip(),
                    option_a=_clean_option(item.get("option_a")),
                    option_b=_clean_option(item.get("option_b")),
                    option_c=_clean_option(item.get("option_c")),
                    option_d=_clean_option(item.get("option_d")),
                    confidence=float(item.get("confidence", 0.5)),
                )
                questions.append(q)
            except (KeyError, ValueError, TypeError) as exc:
                logger.warning("Skipped malformed question entry: %s", exc)

        return questions

    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Vision OCR questions response: %s", exc)
        logger.debug("Raw response:\n%s", raw[:2000])
        return []


def _parse_answers_response(raw: str) -> list[OCRAnswerMapping]:
    """Parse GPT-4o Vision response into OCRAnswerMapping objects."""
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            if text.startswith("json"):
                text = text[4:].strip()

        data = json.loads(text)
        answers: list[OCRAnswerMapping] = []

        for item in data.get("answers", []):
            try:
                answer = item.get("correct_answer", "").strip().lower()
                if answer not in ("a", "b", "c", "d"):
                    logger.warning(
                        "Invalid answer '%s' for Q%s, skipping",
                        answer, item.get("question_number"),
                    )
                    continue

                a = OCRAnswerMapping(
                    question_number=int(item["question_number"]),
                    correct_answer=answer,
                    confidence=float(item.get("confidence", 0.5)),
                )
                answers.append(a)
            except (KeyError, ValueError, TypeError) as exc:
                logger.warning("Skipped malformed answer entry: %s", exc)

        return answers

    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Vision OCR answers response: %s", exc)
        logger.debug("Raw response:\n%s", raw[:2000])
        return []


def _clean_option(val: str | None) -> str | None:
    """Clean an option value, returning None if empty/null."""
    if val is None:
        return None
    cleaned = str(val).strip()
    return cleaned if cleaned else None
