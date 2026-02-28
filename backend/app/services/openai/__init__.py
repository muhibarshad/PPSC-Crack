"""
PPSC Crack — Centralized OpenAI Service
========================================
Re-exports for convenient imports::

    from app.services.openai import openai_service, OpenAICallType
    from app.services.openai import count_tokens, estimate_cost
    from app.services.openai import stream_sse
"""

from app.services.openai.client import openai_service, get_openai_service  # noqa: F401
from app.services.openai.models import OpenAICallType, ModelSpec, MODEL_REGISTRY  # noqa: F401
from app.services.openai.tokens import count_tokens, truncate_to_token_limit  # noqa: F401
from app.services.openai.cost_tracker import CostTracker, cost_tracker  # noqa: F401
from app.services.openai.retry import retry_with_backoff  # noqa: F401
from app.services.openai.streaming import stream_sse  # noqa: F401

__all__ = [
    "openai_service",
    "get_openai_service",
    "OpenAICallType",
    "ModelSpec",
    "MODEL_REGISTRY",
    "count_tokens",
    "truncate_to_token_limit",
    "CostTracker",
    "cost_tracker",
    "retry_with_backoff",
    "stream_sse",
]
