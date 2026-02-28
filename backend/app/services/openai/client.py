"""
Centralized OpenAI Service Client
===================================
Single entry point for every OpenAI interaction.  Provides typed helper
methods for chat completions, vision, embeddings, and streaming — all
with built-in retry logic, token counting, and cost tracking.
"""

from __future__ import annotations

import base64
import logging
import time
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from app.config import settings
from app.services.openai.cost_tracker import CostTracker, cost_tracker as _global_tracker
from app.services.openai.models import (
    MODEL_REGISTRY,
    ModelSpec,
    OpenAICallType,
    GPT_4O,
    GPT_4O_MINI,
    TEXT_EMBEDDING_3_SMALL,
)
from app.services.openai.retry import retry_with_backoff
from app.services.openai.tokens import count_messages_tokens, count_tokens

logger = logging.getLogger(__name__)


class OpenAIService:
    """Thin, opinionated wrapper around the ``openai`` async SDK.

    Instantiate once at startup and inject via FastAPI ``Depends``.

    Features
    --------
    - **Chat completions** (GPT-4o / GPT-4o-mini) with retry & cost logging.
    - **Vision** (image + prompt → text) for scan OCR.
    - **Embeddings** (text-embedding-3-small, 1 536 dims).
    - **Streaming** helper that returns an ``AsyncStream`` ready for SSE.
    - Automatic **token counting** before each call for context-window safety.
    - **Cost tracking** after every call.
    """

    def __init__(
        self,
        api_key: str | None = None,
        org_id: str | None = None,
        tracker: CostTracker | None = None,
    ) -> None:
        self._api_key = api_key or settings.OPENAI_API_KEY
        if not self._api_key:
            logger.warning("OPENAI_API_KEY is empty — OpenAI calls will fail.")

        self.client = AsyncOpenAI(
            api_key=self._api_key,
            organization=org_id or settings.OPENAI_ORG_ID,
            timeout=settings.OPENAI_REQUEST_TIMEOUT,
        )
        self.tracker = tracker or _global_tracker

    # ──────────────────────────────────────────────────────────
    # Chat Completions (non-streaming)
    # ──────────────────────────────────────────────────────────

    async def chat(
        self,
        messages: list[dict[str, str]],
        call_type: OpenAICallType,
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        response_format: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> str:
        """Send a chat completion and return the assistant's text.

        Parameters
        ----------
        messages:
            Standard OpenAI ``messages`` array.
        call_type:
            Logical call type — determines which model to use when
            *model* is ``None`` and drives cost tracking.
        model:
            Override the model resolved from *call_type*.
        temperature, max_tokens, response_format:
            Forwarded to the API.

        Returns
        -------
        str
            The content of the first choice.
        """
        spec = self._resolve_spec(call_type, model)

        # Pre-flight token check
        prompt_tokens_est = count_messages_tokens(messages, spec.model_name)
        max_ctx = spec.context_window
        if prompt_tokens_est > max_ctx * 0.9:
            logger.warning(
                "Prompt (%d tokens) is near the %d context window for %s",
                prompt_tokens_est, max_ctx, spec.model_name,
            )

        start = time.time()
        response = await retry_with_backoff(
            self.client.chat.completions.create,
            model=spec.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            **kwargs,
        )
        elapsed_ms = (time.time() - start) * 1_000

        usage = response.usage
        self.tracker.record(
            call_type=call_type,
            spec=spec,
            prompt_tokens=usage.prompt_tokens if usage else prompt_tokens_est,
            completion_tokens=usage.completion_tokens if usage else 0,
            latency_ms=elapsed_ms,
        )

        return response.choices[0].message.content or ""

    # ──────────────────────────────────────────────────────────
    # Chat Completions (streaming) — returns raw AsyncStream
    # ──────────────────────────────────────────────────────────

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        call_type: OpenAICallType,
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ):
        """Start a streamed chat completion.

        Returns the raw ``AsyncStream[ChatCompletionChunk]`` so the caller
        can wrap it with :func:`stream_sse` or iterate manually.

        Usage::

            stream = await svc.chat_stream(messages, OpenAICallType.STORY_GENERATION)
            return stream_sse(stream, OpenAICallType.STORY_GENERATION, GPT_4O)
        """
        spec = self._resolve_spec(call_type, model)

        return await retry_with_backoff(
            self.client.chat.completions.create,
            model=spec.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            stream_options={"include_usage": True},
            **kwargs,
        )

    # ──────────────────────────────────────────────────────────
    # Convenience: Paper Processing
    # ──────────────────────────────────────────────────────────

    async def process_paper(
        self,
        system_prompt: str,
        paper_text: str,
        *,
        temperature: float = 0.3,
        response_format: dict[str, str] | None = None,
    ) -> str:
        """Analyse / process a past-paper text with GPT-4o."""
        return await self.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": paper_text},
            ],
            call_type=OpenAICallType.PAPER_PROCESSING,
            temperature=temperature,
            response_format=response_format,
        )

    # ──────────────────────────────────────────────────────────
    # Convenience: Story Generation (streaming)
    # ──────────────────────────────────────────────────────────

    async def generate_story_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.8,
    ):
        """Stream a story/mnemonic generation with GPT-4o.

        Returns an ``AsyncStream`` — wrap with ``stream_sse()`` in route.
        """
        return await self.chat_stream(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            call_type=OpenAICallType.STORY_GENERATION,
            temperature=temperature,
        )

    # ──────────────────────────────────────────────────────────
    # Convenience: Prediction Generation
    # ──────────────────────────────────────────────────────────

    async def generate_prediction(
        self,
        system_prompt: str,
        context: str,
        *,
        temperature: float = 0.4,
        response_format: dict[str, str] | None = None,
    ) -> str:
        """Generate exam predictions with GPT-4o."""
        return await self.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context},
            ],
            call_type=OpenAICallType.PREDICTION_GENERATION,
            temperature=temperature,
            response_format=response_format,
        )

    # ──────────────────────────────────────────────────────────
    # Convenience: Classification (GPT-4o-mini)
    # ──────────────────────────────────────────────────────────

    async def classify(
        self,
        system_prompt: str,
        text: str,
        *,
        temperature: float = 0.0,
        response_format: dict[str, str] | None = None,
    ) -> str:
        """Classify text using the lower-cost GPT-4o-mini model."""
        return await self.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            call_type=OpenAICallType.CLASSIFICATION,
            temperature=temperature,
            response_format=response_format,
        )

    # ──────────────────────────────────────────────────────────
    # Vision / OCR (GPT-4o with image input)
    # ──────────────────────────────────────────────────────────

    async def vision_ocr(
        self,
        image_source: str | bytes | Path,
        prompt: str = "Extract all text from this scanned exam paper image. Preserve the original formatting, numbering, and structure as closely as possible.",
        *,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """Send an image to GPT-4o Vision and return extracted text.

        Parameters
        ----------
        image_source:
            - A URL string (``https://…``).
            - Raw bytes of a JPEG/PNG image.
            - A local ``Path`` to an image file.
        prompt:
            Instruction for the model.
        """
        image_content = self._build_image_content(image_source)

        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    image_content,
                ],
            }
        ]

        spec = MODEL_REGISTRY[OpenAICallType.VISION_OCR]

        start = time.time()
        response = await retry_with_backoff(
            self.client.chat.completions.create,
            model=spec.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        elapsed_ms = (time.time() - start) * 1_000

        usage = response.usage
        self.tracker.record(
            call_type=OpenAICallType.VISION_OCR,
            spec=spec,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            latency_ms=elapsed_ms,
            metadata={"image_type": type(image_source).__name__},
        )

        return response.choices[0].message.content or ""

    # ──────────────────────────────────────────────────────────
    # Embeddings (text-embedding-3-small, 1536d)
    # ──────────────────────────────────────────────────────────

    async def embed(
        self,
        texts: str | list[str],
        *,
        call_type: OpenAICallType = OpenAICallType.EMBEDDING,
    ) -> list[list[float]]:
        """Generate embeddings for one or more texts.

        Returns
        -------
        list[list[float]]
            A list of 1 536-dimension embedding vectors.
        """
        if isinstance(texts, str):
            texts = [texts]

        spec = MODEL_REGISTRY[call_type]

        # Token count for cost estimation
        total_input_tokens = sum(count_tokens(t, spec.model_name) for t in texts)

        start = time.time()
        response = await retry_with_backoff(
            self.client.embeddings.create,
            model=spec.model_name,
            input=texts,
            dimensions=settings.OPENAI_EMBEDDING_DIMENSIONS,
        )
        elapsed_ms = (time.time() - start) * 1_000

        usage = response.usage
        self.tracker.record(
            call_type=call_type,
            spec=spec,
            prompt_tokens=usage.total_tokens if usage else total_input_tokens,
            completion_tokens=0,
            latency_ms=elapsed_ms,
            metadata={"batch_size": len(texts)},
        )

        return [item.embedding for item in response.data]

    async def embed_single(self, text: str) -> list[float]:
        """Convenience: embed a single string and return one vector."""
        vectors = await self.embed(text)
        return vectors[0]

    # ──────────────────────────────────────────────────────────
    # Internals
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _resolve_spec(call_type: OpenAICallType, model_override: str | None) -> ModelSpec:
        """Look up the ``ModelSpec`` for a call type, with optional override."""
        spec = MODEL_REGISTRY[call_type]
        if model_override and model_override != spec.model_name:
            # Build a copy with the overridden model name
            return ModelSpec(
                model_name=model_override,
                context_window=spec.context_window,
                input_cost_per_1k=spec.input_cost_per_1k,
                output_cost_per_1k=spec.output_cost_per_1k,
                supports_vision=spec.supports_vision,
                supports_streaming=spec.supports_streaming,
            )
        return spec

    @staticmethod
    def _build_image_content(source: str | bytes | Path) -> dict[str, Any]:
        """Create the ``image_url`` content block for the Vision API."""
        if isinstance(source, str) and source.startswith(("http://", "https://")):
            return {
                "type": "image_url",
                "image_url": {"url": source, "detail": "high"},
            }

        # Raw bytes or file path → base64 data URI
        if isinstance(source, Path):
            raw_bytes = source.read_bytes()
            suffix = source.suffix.lower().lstrip(".")
        elif isinstance(source, bytes):
            raw_bytes = source
            suffix = "png"
        else:
            raise ValueError(f"Unsupported image_source type: {type(source)}")

        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(
            suffix, "image/png"
        )
        b64 = base64.b64encode(raw_bytes).decode()
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "high"},
        }


# ══════════════════════════════════════════════════════════════
# Singleton & FastAPI Dependency
# ══════════════════════════════════════════════════════════════

_service: OpenAIService | None = None


def get_openai_service() -> OpenAIService:
    """FastAPI dependency — returns the singleton ``OpenAIService``.

    Usage::

        @router.post("/process")
        async def process(openai: OpenAIService = Depends(get_openai_service)):
            result = await openai.process_paper(system, text)
    """
    global _service
    if _service is None:
        _service = OpenAIService()
    return _service


# Direct import convenience
openai_service = get_openai_service
