"""
Streaming SSE Wrapper
======================
Wraps OpenAI streamed chat completions into FastAPI-compatible
Server-Sent Events (``text/event-stream``) responses.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from fastapi.responses import StreamingResponse
from openai import AsyncStream
from openai.types.chat import ChatCompletionChunk

from app.services.openai.cost_tracker import CostTracker, cost_tracker as _global_tracker
from app.services.openai.models import ModelSpec, OpenAICallType

logger = logging.getLogger(__name__)


async def _sse_generator(
    stream: AsyncStream[ChatCompletionChunk],
    call_type: OpenAICallType,
    spec: ModelSpec,
    tracker: CostTracker,
    start_time: float,
    metadata: dict[str, Any] | None = None,
) -> AsyncIterator[str]:
    """Yield ``data: …\\n\\n`` lines from an OpenAI streamed response.

    Event types emitted:

    - ``data: {"token": "…"}``   — each content delta
    - ``data: {"done": true, "usage": {…}}`` — final summary
    - ``data: [DONE]``           — SSE termination sentinel
    """
    collected_content: list[str] = []
    prompt_tokens = 0
    completion_tokens = 0

    try:
        async for chunk in stream:
            choice = chunk.choices[0] if chunk.choices else None

            # Accumulate usage if the API returns it on the final chunk
            if chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens
                completion_tokens = chunk.usage.completion_tokens

            if choice and choice.delta and choice.delta.content:
                token_text = choice.delta.content
                collected_content.append(token_text)
                yield f"data: {json.dumps({'token': token_text})}\n\n"

            # Check for stop
            if choice and choice.finish_reason:
                break

    except Exception as exc:
        logger.exception("Error during OpenAI streaming: %s", exc)
        yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        yield "data: [DONE]\n\n"
        return

    # ── Final summary ────────────────────────────────────────
    elapsed_ms = (time.time() - start_time) * 1_000
    full_text = "".join(collected_content)

    # If the API didn't report token counts, estimate from content
    if completion_tokens == 0:
        from app.services.openai.tokens import count_tokens
        completion_tokens = count_tokens(full_text, spec.model_name)

    tracker.record(
        call_type=call_type,
        spec=spec,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=elapsed_ms,
        metadata=metadata,
    )

    done_payload = {
        "done": True,
        "full_text": full_text,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
        "latency_ms": round(elapsed_ms, 2),
    }
    yield f"data: {json.dumps(done_payload)}\n\n"
    yield "data: [DONE]\n\n"


def stream_sse(
    stream: AsyncStream[ChatCompletionChunk],
    call_type: OpenAICallType,
    spec: ModelSpec,
    *,
    tracker: CostTracker | None = None,
    metadata: dict[str, Any] | None = None,
) -> StreamingResponse:
    """Return a FastAPI ``StreamingResponse`` wrapping an OpenAI stream.

    Usage in a route::

        @router.get("/generate-story")
        async def generate_story(openai: OpenAIService = Depends(get_openai_service)):
            stream = await openai.client.chat.completions.create(
                model="gpt-4o", messages=[...], stream=True,
                stream_options={"include_usage": True},
            )
            return stream_sse(stream, OpenAICallType.STORY_GENERATION, GPT_4O)
    """
    return StreamingResponse(
        _sse_generator(
            stream=stream,
            call_type=call_type,
            spec=spec,
            tracker=tracker or _global_tracker,
            start_time=time.time(),
            metadata=metadata,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
