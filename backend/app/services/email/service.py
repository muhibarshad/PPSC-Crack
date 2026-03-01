"""
Email Service — Resend integration for all transactional emails.
================================================================
Handles:
  • Sending emails via Resend API
  • Respecting per-user email preferences
  • Logging every email sent/failed to ``email_logs`` table
  • High-level convenience methods for each email type

Usage::

    from app.services.email import get_email_service

    email_svc = get_email_service()
    await email_svc.send_welcome(db, user)
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

import resend
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.email_log import EmailLog
from app.models.email_preference import EmailPreference
from app.models.user import User

from app.services.email.templates.welcome import render_welcome_email
from app.services.email.templates.subscription_confirmation import render_subscription_confirmation_email
from app.services.email.templates.subscription_expiry import render_subscription_expiry_email
from app.services.email.templates.new_prediction import render_new_prediction_email
from app.services.email.templates.weekly_digest import render_weekly_digest_email
from app.services.email.templates.password_reset import render_password_reset_email

logger = logging.getLogger(__name__)


class EmailService:
    """Transactional email service backed by Resend."""

    def __init__(self) -> None:
        resend.api_key = settings.RESEND_API_KEY
        self._from_email = settings.RESEND_FROM_EMAIL
        self._reply_to = settings.RESEND_REPLY_TO

    # ─────────────────────────────────────────────────────────
    # Low-level send
    # ─────────────────────────────────────────────────────────

    async def _send(
        self,
        to_email: str,
        subject: str,
        html: str,
        email_type: str,
        user_id: UUID | None = None,
        db: AsyncSession | None = None,
        metadata: dict | None = None,
        tags: list[dict] | None = None,
    ) -> str | None:
        """Send an email via Resend and log the result.

        Returns the Resend message ID on success, ``None`` on failure.
        """
        resend_id: str | None = None
        error_msg: str | None = None
        status = "sent"

        try:
            params: dict = {
                "from_": self._from_email,
                "to": [to_email],
                "subject": subject,
                "html": html,
                "reply_to": self._reply_to,
            }
            if tags:
                params["tags"] = tags

            response = resend.Emails.send(params)
            resend_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)
            logger.info("Email sent: type=%s to=%s resend_id=%s", email_type, to_email, resend_id)

        except Exception as exc:
            error_msg = str(exc)
            status = "failed"
            logger.error("Email failed: type=%s to=%s error=%s", email_type, to_email, error_msg)

        # Log to database
        if db is not None:
            log_entry = EmailLog(
                user_id=user_id,
                to_email=to_email,
                email_type=email_type,
                subject=subject,
                resend_id=resend_id,
                status=status,
                metadata_json=metadata,
                error_message=error_msg,
            )
            db.add(log_entry)
            try:
                await db.flush()
            except Exception:
                logger.exception("Failed to log email to database")

        return resend_id

    # ─────────────────────────────────────────────────────────
    # Preference check
    # ─────────────────────────────────────────────────────────

    async def _check_preference(
        self, db: AsyncSession, user_id: UUID, email_type: str
    ) -> bool:
        """Return True if the user has opted into this email type."""
        result = await db.execute(
            select(EmailPreference).where(EmailPreference.user_id == user_id)
        )
        pref = result.scalar_one_or_none()
        if pref is None:
            return True  # No preference row = all emails enabled
        return getattr(pref, email_type, True)

    async def ensure_preferences_exist(
        self, db: AsyncSession, user_id: UUID
    ) -> EmailPreference:
        """Create default email preferences for a user if they don't exist."""
        result = await db.execute(
            select(EmailPreference).where(EmailPreference.user_id == user_id)
        )
        pref = result.scalar_one_or_none()
        if pref is None:
            pref = EmailPreference(user_id=user_id)
            db.add(pref)
            await db.flush()
            await db.refresh(pref)
        return pref

    # ═════════════════════════════════════════════════════════
    # High-level email methods
    # ═════════════════════════════════════════════════════════

    async def send_welcome(
        self,
        db: AsyncSession,
        user: User,
        confirmation_url: str | None = None,
    ) -> str | None:
        """Send welcome email on registration."""
        if not await self._check_preference(db, user.id, "welcome"):
            logger.info("Welcome email skipped (opted out): user=%s", user.id)
            return None

        email_data = render_welcome_email(
            user_name=user.name,
            confirmation_url=confirmation_url,
        )
        return await self._send(
            to_email=user.email,
            subject=email_data["subject"],
            html=email_data["html"],
            email_type="welcome",
            user_id=user.id,
            db=db,
            tags=[{"name": "category", "value": "welcome"}],
        )

    async def send_subscription_confirmation(
        self,
        db: AsyncSession,
        user: User,
        plan_name: str,
        amount: str,
        currency: str = "PKR",
        renewal_date: datetime | str | None = None,
        payment_method: str = "Card",
    ) -> str | None:
        """Send subscription confirmation after successful payment."""
        if not await self._check_preference(db, user.id, "subscription_confirmation"):
            logger.info("Subscription confirmation email skipped: user=%s", user.id)
            return None

        email_data = render_subscription_confirmation_email(
            user_name=user.name,
            plan_name=plan_name,
            amount=amount,
            currency=currency,
            renewal_date=renewal_date,
            payment_method=payment_method,
        )
        return await self._send(
            to_email=user.email,
            subject=email_data["subject"],
            html=email_data["html"],
            email_type="subscription_confirmation",
            user_id=user.id,
            db=db,
            metadata={"plan": plan_name, "amount": amount, "currency": currency},
            tags=[{"name": "category", "value": "subscription"}],
        )

    async def send_subscription_expiry_warning(
        self,
        db: AsyncSession,
        user: User,
        plan_name: str,
        expiry_date: datetime | str,
        days_remaining: int = 3,
    ) -> str | None:
        """Send subscription expiry warning (3 days before)."""
        if not await self._check_preference(db, user.id, "subscription_expiry_warning"):
            logger.info("Expiry warning email skipped: user=%s", user.id)
            return None

        email_data = render_subscription_expiry_email(
            user_name=user.name,
            plan_name=plan_name,
            expiry_date=expiry_date,
            days_remaining=days_remaining,
        )
        return await self._send(
            to_email=user.email,
            subject=email_data["subject"],
            html=email_data["html"],
            email_type="subscription_expiry_warning",
            user_id=user.id,
            db=db,
            metadata={"plan": plan_name, "days_remaining": days_remaining},
            tags=[{"name": "category", "value": "subscription"}],
        )

    async def send_new_prediction(
        self,
        db: AsyncSession,
        user: User,
        job_type_name: str,
        prediction_title: str,
        prediction_date: str,
        total_questions: int,
        prediction_id: str,
    ) -> str | None:
        """Notify a premium user about a new predicted paper."""
        if not await self._check_preference(db, user.id, "new_predicted_paper"):
            logger.info("Prediction email skipped: user=%s", user.id)
            return None

        email_data = render_new_prediction_email(
            user_name=user.name,
            job_type_name=job_type_name,
            prediction_title=prediction_title,
            prediction_date=prediction_date,
            total_questions=total_questions,
            prediction_id=prediction_id,
        )
        return await self._send(
            to_email=user.email,
            subject=email_data["subject"],
            html=email_data["html"],
            email_type="new_predicted_paper",
            user_id=user.id,
            db=db,
            metadata={"prediction_id": prediction_id, "job_type": job_type_name},
            tags=[{"name": "category", "value": "prediction"}],
        )

    async def send_weekly_digest(
        self,
        db: AsyncSession,
        user: User,
        week_label: str,
        items: list[dict],
        total_items_count: int,
    ) -> str | None:
        """Send weekly current affairs digest (free + premium)."""
        if not await self._check_preference(db, user.id, "weekly_current_affairs"):
            logger.info("Weekly digest email skipped: user=%s", user.id)
            return None

        email_data = render_weekly_digest_email(
            user_name=user.name,
            week_label=week_label,
            items=items,
            total_items_count=total_items_count,
            is_premium=user.is_premium,
        )
        return await self._send(
            to_email=user.email,
            subject=email_data["subject"],
            html=email_data["html"],
            email_type="weekly_current_affairs",
            user_id=user.id,
            db=db,
            metadata={"week": week_label, "items_count": total_items_count},
            tags=[{"name": "category", "value": "digest"}],
        )

    async def send_password_reset(
        self,
        db: AsyncSession,
        user: User,
        reset_url: str,
        expires_in_minutes: int = 60,
    ) -> str | None:
        """Send password reset email. Always sent (preference check still logged)."""
        # Password reset is always sent for security, but we log preference
        email_data = render_password_reset_email(
            user_name=user.name,
            reset_url=reset_url,
            expires_in_minutes=expires_in_minutes,
        )
        return await self._send(
            to_email=user.email,
            subject=email_data["subject"],
            html=email_data["html"],
            email_type="password_reset",
            user_id=user.id,
            db=db,
            tags=[{"name": "category", "value": "auth"}],
        )

    # ─────────────────────────────────────────────────────────
    # Batch helpers
    # ─────────────────────────────────────────────────────────

    async def send_prediction_to_subscribers(
        self,
        db: AsyncSession,
        job_type_id: UUID,
        job_type_name: str,
        prediction_title: str,
        prediction_date: str,
        total_questions: int,
        prediction_id: str,
    ) -> int:
        """Notify all premium users who selected this job type.

        Returns count of emails sent.
        """
        from sqlalchemy import and_
        from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID

        result = await db.execute(
            select(User).where(
                and_(
                    User.is_premium.is_(True),
                    User.selected_job_types.any(job_type_id),
                )
            )
        )
        users = result.scalars().all()

        sent = 0
        for user in users:
            msg_id = await self.send_new_prediction(
                db=db,
                user=user,
                job_type_name=job_type_name,
                prediction_title=prediction_title,
                prediction_date=prediction_date,
                total_questions=total_questions,
                prediction_id=prediction_id,
            )
            if msg_id:
                sent += 1

        logger.info(
            "Prediction notification: job_type=%s sent=%d/%d",
            job_type_name, sent, len(users),
        )
        return sent


# ── Singleton ────────────────────────────────────────────────
_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """Return (and lazily create) the global EmailService instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
