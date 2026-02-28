"""
Retry Logic with Exponential Backoff
======================================
Wraps async callables with configurable retry behaviour, specifically
tuned for OpenAI API error semantics (rate-limits, transient failures).
"""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

# HTTP status codes that are safe to retry
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_retryable(exc: BaseException) -> bool:
    """Decide whether *exc* warrants a retry."""
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, (APIConnectionError, APITimeoutError)):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code in _RETRYABLE_STATUS_CODES:
        return True
    return False


async def retry_with_backoff(
    fn: Callable[..., Awaitable[T]],
    *args: Any,
    max_retries: int | None = None,
    base_delay: float | None = None,
    max_delay: float | None = None,
    **kwargs: Any,
) -> T:
    """Call *fn* with retry + exponential backoff on transient OpenAI errors.

    Parameters
    ----------
    fn:
        An ``async`` callable (e.g. ``client.chat.completions.create``).
    max_retries:
        Override ``settings.OPENAI_MAX_RETRIES``.
    base_delay:
        Override ``settings.OPENAI_RETRY_BASE_DELAY`` (seconds).
    max_delay:
        Override ``settings.OPENAI_RETRY_MAX_DELAY`` (seconds).
    *args, **kwargs:
        Forwarded to *fn*.

    Returns
    -------
    T
        The return value of *fn*.

    Raises
    ------
    The last exception if all retries are exhausted.
    """
    _max_retries = max_retries if max_retries is not None else settings.OPENAI_MAX_RETRIES
    _base_delay = base_delay if base_delay is not None else settings.OPENAI_RETRY_BASE_DELAY
    _max_delay = max_delay if max_delay is not None else settings.OPENAI_RETRY_MAX_DELAY

    last_exc: BaseException | None = None

    for attempt in range(_max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc

            if not _is_retryable(exc) or attempt == _max_retries:
                logger.error(
                    "OpenAI call failed (attempt %d/%d, non-retryable): %s",
                    attempt + 1, _max_retries + 1, exc,
                )
                raise

            # Exponential backoff with full jitter
            delay = min(_base_delay * (2 ** attempt), _max_delay)
            jitter = random.uniform(0, delay)  # noqa: S311
            logger.warning(
                "OpenAI call failed (attempt %d/%d): %s — retrying in %.2fs",
                attempt + 1, _max_retries + 1, exc, jitter,
            )
            await asyncio.sleep(jitter)

    # Should never reach here, but satisfy type-checker
    raise last_exc  # type: ignore[misc]


def with_retry(
    max_retries: int | None = None,
    base_delay: float | None = None,
    max_delay: float | None = None,
) -> Callable:
    """Decorator form of :func:`retry_with_backoff`.

    Usage::

        @with_retry(max_retries=3)
        async def my_openai_call():
            ...
    """

    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_with_backoff(
                fn, *args,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                **kwargs,
            )
        return wrapper

    return decorator
