"""
Cost Tracker — Log & Aggregate OpenAI Token Usage
===================================================
Logs every API call's token usage, model, call type, and estimated cost
to both the application logger and an in-memory running total.

In production you'd persist these to a DB table or push to an analytics
pipeline; the in-memory tracker is a lightweight starting point.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from app.services.openai.models import ModelSpec, OpenAICallType

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """One recorded API call."""

    call_type: OpenAICallType
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    latency_ms: float
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class CostTracker:
    """Thread-safe, in-memory cost tracker for OpenAI calls."""

    def __init__(self) -> None:
        self._records: list[UsageRecord] = []
        self._lock = Lock()

        # Running totals
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_cost_usd = 0.0

    # ── Recording ────────────────────────────────────────────

    def record(
        self,
        call_type: OpenAICallType,
        spec: ModelSpec,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        metadata: dict[str, Any] | None = None,
    ) -> UsageRecord:
        """Record a single API call's token usage and cost."""
        total_tokens = prompt_tokens + completion_tokens
        cost = (
            (prompt_tokens / 1_000) * spec.input_cost_per_1k
            + (completion_tokens / 1_000) * spec.output_cost_per_1k
        )

        rec = UsageRecord(
            call_type=call_type,
            model=spec.model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=round(cost, 8),
            latency_ms=round(latency_ms, 2),
            metadata=metadata or {},
        )

        with self._lock:
            self._records.append(rec)
            self._total_prompt_tokens += prompt_tokens
            self._total_completion_tokens += completion_tokens
            self._total_cost_usd += cost

        logger.info(
            "OpenAI %-22s | model=%-18s | in=%5d  out=%5d  total=%5d | $%.6f | %7.0f ms",
            call_type.value,
            spec.model_name,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            cost,
            latency_ms,
        )

        return rec

    # ── Summaries ────────────────────────────────────────────

    def summary(self) -> dict[str, Any]:
        """Return a snapshot of running totals."""
        with self._lock:
            return {
                "total_calls": len(self._records),
                "total_prompt_tokens": self._total_prompt_tokens,
                "total_completion_tokens": self._total_completion_tokens,
                "total_tokens": self._total_prompt_tokens + self._total_completion_tokens,
                "estimated_total_cost_usd": round(self._total_cost_usd, 6),
            }

    def summary_by_call_type(self) -> dict[str, dict[str, Any]]:
        """Return totals grouped by call type."""
        groups: dict[str, dict[str, Any]] = {}
        with self._lock:
            for rec in self._records:
                key = rec.call_type.value
                if key not in groups:
                    groups[key] = {
                        "calls": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "cost_usd": 0.0,
                    }
                g = groups[key]
                g["calls"] += 1
                g["prompt_tokens"] += rec.prompt_tokens
                g["completion_tokens"] += rec.completion_tokens
                g["cost_usd"] = round(g["cost_usd"] + rec.estimated_cost_usd, 8)
        return groups

    def recent(self, n: int = 20) -> list[UsageRecord]:
        """Return the last *n* records."""
        with self._lock:
            return list(self._records[-n:])

    def reset(self) -> None:
        """Clear all records and totals (useful in tests)."""
        with self._lock:
            self._records.clear()
            self._total_prompt_tokens = 0
            self._total_completion_tokens = 0
            self._total_cost_usd = 0.0


# ── Singleton ────────────────────────────────────────────────
cost_tracker = CostTracker()
