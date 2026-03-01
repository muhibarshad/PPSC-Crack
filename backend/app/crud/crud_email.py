"""CRUD helpers for EmailPreference and EmailLog models."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_preference import EmailPreference
from app.models.email_log import EmailLog


# ═══════════════════════════════════════════════════════════
# Email Preferences
# ═══════════════════════════════════════════════════════════

class CRUDEmailPreference:
    """CRUD operations for email_preferences table."""

    async def get_by_user(
        self, db: AsyncSession, *, user_id: UUID
    ) -> EmailPreference | None:
        result = await db.execute(
            select(EmailPreference).where(EmailPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self, db: AsyncSession, *, user_id: UUID
    ) -> EmailPreference:
        """Return existing preferences or create with defaults."""
        pref = await self.get_by_user(db, user_id=user_id)
        if pref is None:
            pref = EmailPreference(user_id=user_id)
            db.add(pref)
            await db.flush()
            await db.refresh(pref)
        return pref

    async def update(
        self, db: AsyncSession, *, user_id: UUID, updates: dict
    ) -> EmailPreference:
        """Update email preferences for a user."""
        pref = await self.get_or_create(db, user_id=user_id)
        for key, value in updates.items():
            if hasattr(pref, key) and value is not None:
                setattr(pref, key, value)
        await db.flush()
        await db.refresh(pref)
        return pref


# ═══════════════════════════════════════════════════════════
# Email Logs
# ═══════════════════════════════════════════════════════════

class CRUDEmailLog:
    """CRUD operations for email_logs table."""

    async def get_user_logs(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        email_type: str | None = None,
    ) -> tuple[list[EmailLog], int]:
        """Get paginated email logs for a user."""
        query = select(EmailLog).where(EmailLog.user_id == user_id)
        count_query = select(func.count()).select_from(EmailLog).where(
            EmailLog.user_id == user_id
        )

        if email_type:
            query = query.where(EmailLog.email_type == email_type)
            count_query = count_query.where(EmailLog.email_type == email_type)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(desc(EmailLog.sent_at)).limit(limit).offset(offset)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_all_logs(
        self,
        db: AsyncSession,
        *,
        limit: int = 100,
        offset: int = 0,
        email_type: str | None = None,
        status: str | None = None,
    ) -> tuple[list[EmailLog], int]:
        """Admin: get all email logs with optional filters."""
        query = select(EmailLog)
        count_query = select(func.count()).select_from(EmailLog)

        if email_type:
            query = query.where(EmailLog.email_type == email_type)
            count_query = count_query.where(EmailLog.email_type == email_type)
        if status:
            query = query.where(EmailLog.status == status)
            count_query = count_query.where(EmailLog.status == status)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(desc(EmailLog.sent_at)).limit(limit).offset(offset)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total


# ── Module-level singletons ──────────────────────────────────
crud_email_preference = CRUDEmailPreference()
crud_email_log = CRUDEmailLog()
