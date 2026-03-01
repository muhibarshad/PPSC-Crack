"""
PPSC Crack — Email Preferences & Logs Endpoints
==================================================
GET  /email/preferences        — get current user's email preferences
PUT  /email/preferences        — update email preferences
GET  /email/logs               — get current user's email history
POST /email/test               — (admin) send a test email

Admin:
GET  /admin/email/logs         — all email logs with filters
POST /admin/email/send-digest  — manually trigger weekly digest
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.crud import crud_email_preference, crud_email_log
from app.dependencies import DBSession, get_current_user
from app.models.user import User
from app.schemas.email import (
    EmailPreferenceResponse,
    EmailPreferenceUpdate,
    EmailLogListResponse,
    EmailLogResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ═══════════════════════════════════════════════════════════
# GET /email/preferences
# ═══════════════════════════════════════════════════════════

@router.get("/email/preferences", response_model=EmailPreferenceResponse)
async def get_email_preferences(
    db: DBSession,
    user: User = Depends(get_current_user),
):
    """Return the current user's email notification preferences."""
    pref = await crud_email_preference.get_or_create(db, user_id=user.id)
    await db.commit()
    return pref


# ═══════════════════════════════════════════════════════════
# PUT /email/preferences
# ═══════════════════════════════════════════════════════════

@router.put("/email/preferences", response_model=EmailPreferenceResponse)
async def update_email_preferences(
    body: EmailPreferenceUpdate,
    db: DBSession,
    user: User = Depends(get_current_user),
):
    """Update the current user's email notification preferences."""
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update.",
        )
    pref = await crud_email_preference.update(db, user_id=user.id, updates=updates)
    await db.commit()
    return pref


# ═══════════════════════════════════════════════════════════
# GET /email/logs
# ═══════════════════════════════════════════════════════════

@router.get("/email/logs", response_model=EmailLogListResponse)
async def get_my_email_logs(
    db: DBSession,
    user: User = Depends(get_current_user),
    email_type: str | None = Query(None, description="Filter by email type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Return the current user's email log history."""
    items, total = await crud_email_log.get_user_logs(
        db, user_id=user.id, limit=limit, offset=offset, email_type=email_type,
    )
    return EmailLogListResponse(
        items=[EmailLogResponse.model_validate(i) for i in items],
        total=total,
    )
