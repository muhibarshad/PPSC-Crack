"""
PPSC Crack — Admin Analytics Endpoint
=======================================
Serves DAU and conversion funnel data for the admin analytics page.
Aggregates from the activity_log and user tables.
"""

from datetime import date, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin

router = APIRouter(prefix="/admin/analytics", tags=["Admin Analytics"])


@router.get("")
async def get_admin_analytics(
    period: Literal["7d", "30d", "90d"] = Query("30d"),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Return DAU + conversion funnel for the admin analytics dashboard."""
    days = {"7d": 7, "30d": 30, "90d": 90}[period]
    start_date = date.today() - timedelta(days=days)

    # ── DAU: count distinct users per day from activity_log ──
    dau_query = text("""
        SELECT
            DATE(created_at) as day,
            COUNT(DISTINCT user_id) as active_users
        FROM activity_log
        WHERE created_at >= :start_date
        GROUP BY DATE(created_at)
        ORDER BY day
    """)
    dau_result = await db.execute(dau_query, {"start_date": start_date})
    dau_rows = dau_result.fetchall()

    dau_data = [
        {"date": str(row[0]), "active_users": row[1]}
        for row in dau_rows
    ]

    # If no activity_log table yet, return empty DAU
    if not dau_data:
        dau_data = [
            {"date": str(start_date + timedelta(days=i)), "active_users": 0}
            for i in range(days)
        ]

    # ── Total users ──
    total_result = await db.execute(text("SELECT COUNT(*) FROM users"))
    total_users = total_result.scalar() or 0

    # ── Funnel steps ──
    # Step 1: Registered (all users)
    registered = total_users

    # Step 2: Completed onboarding (has at least one job type selected)
    onboarded_result = await db.execute(text(
        "SELECT COUNT(DISTINCT user_id) FROM user_job_types"
    ))
    onboarded = onboarded_result.scalar() or 0

    # Step 3: Started first topic (has topic_progress record)
    first_topic_result = await db.execute(text(
        "SELECT COUNT(DISTINCT user_id) FROM topic_progress"
    ))
    first_topic = first_topic_result.scalar() or 0

    # Step 4: Took practice test
    practice_result = await db.execute(text(
        "SELECT COUNT(DISTINCT user_id) FROM practice_test_results"
    ))
    practice_count = practice_result.scalar() or 0

    # Step 5: Subscribed (premium)
    subscribed_result = await db.execute(text(
        "SELECT COUNT(*) FROM users WHERE subscription_tier != 'free'"
    ))
    subscribed = subscribed_result.scalar() or 0

    funnel = [
        {"step": "registered", "label": "Registered", "count": registered, "color": "rgba(167, 139, 250, 0.6)"},
        {"step": "onboarded", "label": "Completed Onboarding", "count": onboarded, "color": "rgba(139, 92, 246, 0.6)"},
        {"step": "first_topic", "label": "Started First Topic", "count": first_topic, "color": "rgba(232, 121, 249, 0.6)"},
        {"step": "practice_test", "label": "Took Practice Test", "count": practice_count, "color": "rgba(56, 189, 248, 0.6)"},
        {"step": "subscribed", "label": "Subscribed (Premium)", "count": subscribed, "color": "rgba(52, 211, 153, 0.6)"},
    ]

    # Average DAU
    dau_values = [d["active_users"] for d in dau_data]
    dau_avg = round(sum(dau_values) / max(len(dau_values), 1))

    return {
        "dau": dau_data,
        "funnel": funnel,
        "total_users": total_users,
        "dau_average": dau_avg,
    }
