"""
PPSC Crack — Sentry Integration for FastAPI
=============================================
Captures: unhandled exceptions, API errors, failed AI calls, payment failures.
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.config import settings


def init_sentry():
    """Initialize Sentry SDK. Call this once at app startup."""
    dsn = getattr(settings, 'SENTRY_DSN', '')
    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        environment="production" if not settings.DEBUG else "development",
        release=f"ppsc-crack-backend@{settings.APP_VERSION}",
        traces_sample_rate=0.2,
        profiles_sample_rate=0.1,
        send_default_pii=False,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
            HttpxIntegration(),
            CeleryIntegration(),
            LoggingIntegration(level=None, event_level="ERROR"),
        ],
        before_send=_before_send,
    )


def _before_send(event, hint):
    """Tag payment and AI errors for alerting."""
    exc = hint.get("exc_info")
    if exc:
        exc_value = str(exc[1]) if exc[1] else ""
        if "stripe" in exc_value.lower() or "payment" in exc_value.lower():
            event.setdefault("tags", {})["category"] = "payment_failure"
            event["level"] = "fatal"
        if "openai" in exc_value.lower() or "ai" in exc_value.lower():
            event.setdefault("tags", {})["category"] = "ai_failure"
    return event


def capture_ai_error(error: Exception, context: dict | None = None):
    """Explicitly capture an AI/OpenAI error with context."""
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("category", "ai_failure")
        if context:
            scope.set_context("ai_context", context)
        sentry_sdk.capture_exception(error)


def capture_payment_error(error: Exception, context: dict | None = None):
    """Explicitly capture a payment error with context."""
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("category", "payment_failure")
        scope.level = "fatal"
        if context:
            scope.set_context("payment_context", context)
        sentry_sdk.capture_exception(error)
