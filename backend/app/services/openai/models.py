"""
OpenAI Model Registry & Call-Type Definitions
===============================================
Single source of truth for model names, context windows, and per-token costs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OpenAICallType(str, Enum):
    """Logical call types the application uses."""

    PAPER_PROCESSING = "paper_processing"
    STORY_GENERATION = "story_generation"
    PREDICTION_GENERATION = "prediction_generation"
    CLASSIFICATION = "classification"
    LOW_COST_TASK = "low_cost_task"
    EMBEDDING = "embedding"
    VISION_OCR = "vision_ocr"
    MCQ_GENERATION = "mcq_generation"


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """Specification for a single OpenAI model."""

    model_name: str
    context_window: int  # max tokens
    # Pricing per 1 000 tokens (USD) — update as OpenAI changes
    input_cost_per_1k: float
    output_cost_per_1k: float
    supports_vision: bool = False
    supports_streaming: bool = True
    embedding_dimensions: int | None = None


# ── Model Catalogue (prices as of Feb 2026) ─────────────────
GPT_4O = ModelSpec(
    model_name="gpt-4o",
    context_window=128_000,
    input_cost_per_1k=0.0025,
    output_cost_per_1k=0.0100,
    supports_vision=True,
)

GPT_4O_MINI = ModelSpec(
    model_name="gpt-4o-mini",
    context_window=128_000,
    input_cost_per_1k=0.000150,
    output_cost_per_1k=0.000600,
)

TEXT_EMBEDDING_3_SMALL = ModelSpec(
    model_name="text-embedding-3-small",
    context_window=8_191,
    input_cost_per_1k=0.00002,
    output_cost_per_1k=0.0,  # embeddings have no output tokens
    supports_streaming=False,
    embedding_dimensions=1536,
)

# ── Registry: call-type → model spec ────────────────────────
MODEL_REGISTRY: dict[OpenAICallType, ModelSpec] = {
    OpenAICallType.PAPER_PROCESSING: GPT_4O,
    OpenAICallType.STORY_GENERATION: GPT_4O,
    OpenAICallType.PREDICTION_GENERATION: GPT_4O,
    OpenAICallType.CLASSIFICATION: GPT_4O_MINI,
    OpenAICallType.LOW_COST_TASK: GPT_4O_MINI,
    OpenAICallType.EMBEDDING: TEXT_EMBEDDING_3_SMALL,
    OpenAICallType.VISION_OCR: GPT_4O,
    OpenAICallType.MCQ_GENERATION: GPT_4O,
}
