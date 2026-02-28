"""
Paper Text Parser
==================
Parses raw pasted text of 100 MCQs + answer key into structured objects.

Supports common PPSC exam formats:
- ``1. What is the capital of Pakistan?``
- ``1) What is the capital of Pakistan?``
- ``Q1. What is the capital of Pakistan?``
- Options: ``(A)`` / ``A)`` / ``A.`` / ``a.`` etc.
- Answer key: ``1-A  2-B  3-C`` or ``1. A  2. B`` or ``1=A 2=B``
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════

@dataclass
class ParsedQuestion:
    """A single parsed MCQ."""
    question_number: int
    question_text: str
    option_a: str | None = None
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None
    correct_answer: str | None = None  # a/b/c/d (lowercase)
    needs_review: bool = False
    review_reason: str | None = None


@dataclass
class ParseResult:
    """Full parse output for a pasted paper."""
    questions: list[ParsedQuestion] = field(default_factory=list)
    answer_map: dict[int, str] = field(default_factory=dict)
    unmapped_questions: list[int] = field(default_factory=list)
    unmapped_answers: list[int] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    total_parsed: int = 0
    total_mapped: int = 0


# ═══════════════════════════════════════════════════════════
# Question Parsing
# ═══════════════════════════════════════════════════════════

# Pattern: question number at the start of a line
_Q_NUM_RE = re.compile(
    r"^(?:Q\.?\s*)?(\d{1,3})\s*[.):\-]\s*(.+)",
    re.IGNORECASE,
)

# Pattern: option line  (A) text  or  A. text  or  A) text  or  a) text
_OPTION_RE = re.compile(
    r"^\s*\(?([A-Da-d])\s*[.):\-]\s*(.+)",
)


def parse_questions_text(raw_text: str) -> list[ParsedQuestion]:
    """Parse pasted questions text into structured ``ParsedQuestion`` objects.

    Handles multi-line question text and options in various PPSC formats.
    """
    lines = raw_text.strip().splitlines()
    questions: list[ParsedQuestion] = []
    current_q: ParsedQuestion | None = None
    current_text_lines: list[str] = []

    def _flush_question():
        nonlocal current_q, current_text_lines
        if current_q is not None:
            if current_text_lines:
                current_q.question_text = " ".join(current_text_lines).strip()
            # Flag if missing options or text
            if not current_q.question_text:
                current_q.needs_review = True
                current_q.review_reason = "Empty question text"
            elif not current_q.option_a and not current_q.option_b:
                current_q.needs_review = True
                current_q.review_reason = "No options detected"
            questions.append(current_q)
            current_text_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if this is an option line
        opt_match = _OPTION_RE.match(line)
        if opt_match and current_q is not None:
            letter = opt_match.group(1).lower()
            text = opt_match.group(2).strip()
            if letter == "a":
                current_q.option_a = text
            elif letter == "b":
                current_q.option_b = text
            elif letter == "c":
                current_q.option_c = text
            elif letter == "d":
                current_q.option_d = text
            continue

        # Check if this is a new question number
        q_match = _Q_NUM_RE.match(line)
        if q_match:
            _flush_question()
            q_num = int(q_match.group(1))
            q_text_start = q_match.group(2).strip()
            current_q = ParsedQuestion(question_number=q_num, question_text="")
            current_text_lines = [q_text_start] if q_text_start else []
            continue

        # Continuation of current question text
        if current_q is not None:
            current_text_lines.append(line)

    # Flush last question
    _flush_question()

    return questions


# ═══════════════════════════════════════════════════════════
# Answer Key Parsing
# ═══════════════════════════════════════════════════════════

# Patterns:  1-A  |  1.A  |  1=A  |  1) A  |  1: A
_ANSWER_RE = re.compile(
    r"(\d{1,3})\s*[-=.:)]\s*([A-Da-d])",
)


def parse_answer_key(raw_text: str) -> dict[int, str]:
    """Parse answer key text into ``{question_number: answer_letter}`` mapping.

    answer_letter is normalized to lowercase (a/b/c/d).
    """
    matches = _ANSWER_RE.findall(raw_text)
    return {int(num): letter.lower() for num, letter in matches}


# ═══════════════════════════════════════════════════════════
# Q&A Mapping
# ═══════════════════════════════════════════════════════════

def map_questions_to_answers(
    questions: list[ParsedQuestion],
    answer_map: dict[int, str],
) -> ParseResult:
    """Pair parsed questions with their answers from the answer key.

    - Matched questions get ``correct_answer`` set.
    - Unmatched questions get ``needs_review=True``.
    - Extra answer-key entries with no question are reported.
    """
    result = ParseResult(
        questions=questions,
        answer_map=answer_map,
        total_parsed=len(questions),
    )

    q_numbers = {q.question_number for q in questions}
    a_numbers = set(answer_map.keys())

    # Questions with no answer
    result.unmapped_questions = sorted(q_numbers - a_numbers)
    # Answers with no question
    result.unmapped_answers = sorted(a_numbers - q_numbers)

    mapped_count = 0
    for q in questions:
        if q.question_number in answer_map:
            q.correct_answer = answer_map[q.question_number]
            mapped_count += 1
        else:
            q.needs_review = True
            q.review_reason = (q.review_reason or "") + " | No answer key mapping"

    result.total_mapped = mapped_count

    if result.unmapped_questions:
        result.warnings.append(
            f"{len(result.unmapped_questions)} question(s) have no answer: "
            f"{result.unmapped_questions[:10]}"
        )
    if result.unmapped_answers:
        result.warnings.append(
            f"{len(result.unmapped_answers)} answer(s) have no question: "
            f"{result.unmapped_answers[:10]}"
        )

    logger.info(
        "Paper parse: %d questions, %d mapped, %d unmapped-q, %d unmapped-a",
        result.total_parsed, result.total_mapped,
        len(result.unmapped_questions), len(result.unmapped_answers),
    )

    return result
