"""
PPSC Crack — Admin Email Endpoints
====================================
GET  /admin/email/logs           — all email logs (paginated, filtered)
POST /admin/email/test           — send a test email to any address
POST /admin/email/trigger-digest — manually trigger weekly digest
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr

from app.crud import crud_email_log, crud_user
from app.dependencies import DBSession, get_current_user
from app.models.user import User
from app.schemas.email import EmailLogListResponse, EmailLogResponse
from app.services.email import get_email_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _require_admin(user: User) -> None:
    if user.role not in ("admin", "moderator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required."
        )


# ═══════════════════════════════════════════════════════════
# GET /admin/email/logs
# ═══════════════════════════════════════════════════════════

@router.get("/email/logs", response_model=EmailLogListResponse)
async def admin_email_logs(
    db: DBSession,
    user: User = Depends(get_current_user),
    email_type: str | None = Query(None),
    email_status: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Admin: list all email logs with optional filters."""
    _require_admin(user)
    items, total = await crud_email_log.get_all_logs(
        db, limit=limit, offset=offset, email_type=email_type, status=email_status,
    )
    return EmailLogListResponse(
        items=[EmailLogResponse.model_validate(i) for i in items],
        total=total,
    )


# ═══════════════════════════════════════════════════════════
# POST /admin/email/test
# ═══════════════════════════════════════════════════════════

class TestEmailRequest(BaseModel):
    to_email: EmailStr
    template: str = "welcome"  # welcome | subscription_confirmation | ...


@router.post("/email/test", status_code=status.HTTP_200_OK)
async def admin_send_test_email(
    body: TestEmailRequest,
    db: DBSession,
    user: User = Depends(get_current_user),
):
    """Admin: send a test email using any template."""
    _require_admin(user)

    email_svc = get_email_service()

    # Use the admin user as the fake recipient context
    template_map = {
        "welcome": lambda: email_svc.send_welcome(db, user),
        "password_reset": lambda: email_svc.send_password_reset(
            db, user, reset_url=f"{__import__('app.config', fromlist=['settings']).settings.FRONTEND_URL}/auth/reset-password?token=test-token",
        ),
        "subscription_confirmation": lambda: email_svc.send_subscription_confirmation(
            db, user, plan_name="Pro", amount="999", currency="PKR",
        ),
        "subscription_expiry_warning": lambda: email_svc.send_subscription_expiry_warning(
            db, user, plan_name="Pro", expiry_date="March 10, 2026", days_remaining=3,
        ),
        "new_predicted_paper": lambda: email_svc.send_new_prediction(
            db, user, job_type_name="PMS",
            prediction_title="PMS March 2026 Prediction",
            prediction_date="March 2026", total_questions=100,
            prediction_id="00000000-0000-0000-0000-000000000000",
        ),
    }

    sender = template_map.get(body.template)
    if sender is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown template: {body.template}. Available: {list(template_map.keys())}",
        )

    resend_id = await sender()
    await db.commit()

    return {"message": "Test email sent", "resend_id": resend_id, "template": body.template}


# ═══════════════════════════════════════════════════════════
# POST /admin/email/trigger-digest
# ═══════════════════════════════════════════════════════════

@router.post("/email/trigger-digest", status_code=status.HTTP_202_ACCEPTED)
async def admin_trigger_digest(
    db: DBSession,
    user: User = Depends(get_current_user),
):
    """Admin: manually trigger the weekly current affairs digest."""
    _require_admin(user)

    from app.tasks.email_tasks import send_weekly_digest_task
    task = send_weekly_digest_task.delay()

    return {
        "message": "Weekly digest task queued",
        "task_id": task.id,
    }
