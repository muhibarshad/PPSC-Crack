"""
Celery Tasks — Email Operations
=================================
Background tasks for:
  • Weekly current affairs digest (every Monday 8 AM PKT)
  • Subscription expiry warnings (daily check, 3 days before)
  • New prediction notifications (triggered on publish)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from celery import shared_task

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine inside a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ═══════════════════════════════════════════════════════════
# Weekly Current Affairs Digest
# ═══════════════════════════════════════════════════════════

@shared_task(name="app.tasks.email_tasks.send_weekly_digest_task", bind=True, max_retries=2)
def send_weekly_digest_task(self):
    """Send weekly current affairs digest to all users.

    Scheduled via Celery Beat for every Monday at 8:00 AM PKT.
    """
    logger.info("Starting weekly current affairs digest email task")
    return _run_async(_send_weekly_digest_async())


async def _send_weekly_digest_async():
    """Async implementation of the weekly digest sender."""
    from sqlalchemy import select, and_
    from app.database import SessionManager
    from app.models.user import User
    from app.models.current_affair import CurrentAffairsItem
    from app.services.email import get_email_service

    email_svc = get_email_service()
    sent_count = 0
    error_count = 0

    async with SessionManager() as db:
        # Fetch this week's current affairs (last 7 days)
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        result = await db.execute(
            select(CurrentAffairsItem)
            .where(
                and_(
                    CurrentAffairsItem.created_at >= week_ago,
                    CurrentAffairsItem.status == "approved",
                )
            )
            .order_by(CurrentAffairsItem.relevance_score.desc())
            .limit(20)
        )
        affairs = result.scalars().all()

        if not affairs:
            logger.info("No current affairs items this week — skipping digest")
            return {"sent": 0, "skipped": "no_items"}

        # Build the digest items (top 7 for email)
        today = datetime.now(timezone.utc)
        week_start = today - timedelta(days=7)
        week_label = f"{week_start.strftime('%b %d')} – {today.strftime('%b %d, %Y')}"

        digest_items = []
        for ca in affairs[:7]:
            item = {
                "title": ca.title,
                "summary": ca.summary or ca.title,
                "category": ca.category or "General",
            }
            # Include MCQ if available
            if ca.mcqs_json and isinstance(ca.mcqs_json, list) and len(ca.mcqs_json) > 0:
                mcq = ca.mcqs_json[0]
                item["mcq"] = mcq
            digest_items.append(item)

        # Fetch all active users
        user_result = await db.execute(select(User))
        users = user_result.scalars().all()

        for user in users:
            try:
                msg_id = await email_svc.send_weekly_digest(
                    db=db,
                    user=user,
                    week_label=week_label,
                    items=digest_items,
                    total_items_count=len(affairs),
                )
                if msg_id:
                    sent_count += 1
            except Exception:
                error_count += 1
                logger.exception("Failed to send digest to user=%s", user.id)

        await db.commit()

    logger.info("Weekly digest complete: sent=%d errors=%d", sent_count, error_count)
    return {"sent": sent_count, "errors": error_count}


# ═══════════════════════════════════════════════════════════
# Subscription Expiry Warnings
# ═══════════════════════════════════════════════════════════

@shared_task(name="app.tasks.email_tasks.check_subscription_expiry_task", bind=True, max_retries=2)
def check_subscription_expiry_task(self):
    """Check for subscriptions expiring in 3 days and send warnings.

    Scheduled via Celery Beat daily at 9:00 AM PKT.
    """
    logger.info("Starting subscription expiry check")
    return _run_async(_check_subscription_expiry_async())


async def _check_subscription_expiry_async():
    """Async implementation of the expiry checker."""
    from sqlalchemy import select, and_
    from app.database import SessionManager
    from app.models.user import User
    from app.services.email import get_email_service

    email_svc = get_email_service()
    sent_count = 0

    async with SessionManager() as db:
        now = datetime.now(timezone.utc)
        three_days_later = now + timedelta(days=3)
        # Also check 1-day warning
        one_day_later = now + timedelta(days=1)

        # Users expiring in ~3 days (between 2.5 and 3.5 days)
        result_3d = await db.execute(
            select(User).where(
                and_(
                    User.is_premium.is_(True),
                    User.subscription_expires_at.isnot(None),
                    User.subscription_expires_at >= now + timedelta(days=2, hours=12),
                    User.subscription_expires_at <= now + timedelta(days=3, hours=12),
                )
            )
        )
        users_3d = result_3d.scalars().all()

        for user in users_3d:
            try:
                tier_name = (user.subscription_tier or "Pro").title()
                await email_svc.send_subscription_expiry_warning(
                    db=db,
                    user=user,
                    plan_name=tier_name,
                    expiry_date=user.subscription_expires_at,
                    days_remaining=3,
                )
                sent_count += 1
            except Exception:
                logger.exception("Failed to send 3-day warning to user=%s", user.id)

        # Users expiring in ~1 day (final warning)
        result_1d = await db.execute(
            select(User).where(
                and_(
                    User.is_premium.is_(True),
                    User.subscription_expires_at.isnot(None),
                    User.subscription_expires_at >= now + timedelta(hours=12),
                    User.subscription_expires_at <= now + timedelta(days=1, hours=12),
                )
            )
        )
        users_1d = result_1d.scalars().all()

        for user in users_1d:
            try:
                tier_name = (user.subscription_tier or "Pro").title()
                await email_svc.send_subscription_expiry_warning(
                    db=db,
                    user=user,
                    plan_name=tier_name,
                    expiry_date=user.subscription_expires_at,
                    days_remaining=1,
                )
                sent_count += 1
            except Exception:
                logger.exception("Failed to send 1-day warning to user=%s", user.id)

        await db.commit()

    logger.info("Expiry check complete: warnings_sent=%d", sent_count)
    return {"warnings_sent": sent_count}


# ═══════════════════════════════════════════════════════════
# New Prediction Notification
# ═══════════════════════════════════════════════════════════

@shared_task(name="app.tasks.email_tasks.notify_prediction_published", bind=True, max_retries=2)
def notify_prediction_published(
    self,
    prediction_id: str,
    job_type_id: str,
    job_type_name: str,
    prediction_title: str,
    prediction_date: str,
    total_questions: int,
):
    """Notify premium users when a new predicted paper is published.

    Called explicitly from the admin publish endpoint.
    """
    logger.info("Notifying users about prediction=%s for job_type=%s", prediction_id, job_type_name)
    return _run_async(
        _notify_prediction_async(
            prediction_id=prediction_id,
            job_type_id=job_type_id,
            job_type_name=job_type_name,
            prediction_title=prediction_title,
            prediction_date=prediction_date,
            total_questions=total_questions,
        )
    )


async def _notify_prediction_async(
    prediction_id: str,
    job_type_id: str,
    job_type_name: str,
    prediction_title: str,
    prediction_date: str,
    total_questions: int,
):
    """Async implementation of prediction notification."""
    from uuid import UUID
    from app.database import SessionManager
    from app.services.email import get_email_service

    email_svc = get_email_service()

    async with SessionManager() as db:
        sent = await email_svc.send_prediction_to_subscribers(
            db=db,
            job_type_id=UUID(job_type_id),
            job_type_name=job_type_name,
            prediction_title=prediction_title,
            prediction_date=prediction_date,
            total_questions=total_questions,
            prediction_id=prediction_id,
        )
        await db.commit()

    logger.info("Prediction notification complete: sent=%d", sent)
    return {"sent": sent}
