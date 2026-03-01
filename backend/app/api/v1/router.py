"""
PPSC Crack — API v1 Aggregated Router
=======================================
Mounts all v1 endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    dashboard,
    health,
    job_types,
    learning_path,
    users,
    papers,
    patterns,
    predictions,
    current_affairs,
    stories,
    student_topics,
    practice,
    onboarding,
    student_predictions,
    student_current_affairs,
    student_analytics,
    admin_papers,
    admin_review,
    admin_scan,
    admin_notes,
    admin_predictions,
    admin_current_affairs,
    admin_pattern_analytics,
    admin_dashboard,
    payments,
    email,
    admin_email,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, prefix="/health", tags=["Health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_v1_router.include_router(learning_path.router, prefix="/dashboard", tags=["Learning Path"])
api_v1_router.include_router(job_types.router, prefix="/job-types", tags=["Job Types"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(papers.router, prefix="/papers", tags=["Papers"])
api_v1_router.include_router(patterns.router, prefix="/patterns", tags=["Patterns"])
api_v1_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
api_v1_router.include_router(stories.router, prefix="/stories", tags=["Stories"])
api_v1_router.include_router(
    student_topics.router, tags=["Student — Story Reader"]
)
api_v1_router.include_router(
    practice.router, tags=["Student — Practice Test"]
)
api_v1_router.include_router(
    student_predictions.router, prefix="/student", tags=["Student — Predictions"]
)
api_v1_router.include_router(
    student_current_affairs.router, prefix="/student", tags=["Student — Current Affairs"]
)
api_v1_router.include_router(
    student_analytics.router, prefix="/student", tags=["Student — Analytics"]
)
api_v1_router.include_router(
    current_affairs.router, prefix="/current-affairs", tags=["Current Affairs"]
)
api_v1_router.include_router(
    onboarding.router, prefix="/onboarding", tags=["Onboarding"]
)
api_v1_router.include_router(
    admin_papers.router, prefix="/admin", tags=["Admin — Paper Ingestion"]
)
api_v1_router.include_router(
    admin_review.router, prefix="/admin", tags=["Admin — Review Queue"]
)
api_v1_router.include_router(
    admin_scan.router, prefix="/admin", tags=["Admin — Scan Upload"]
)
api_v1_router.include_router(
    admin_notes.router, prefix="/admin", tags=["Admin — Notes"]
)
api_v1_router.include_router(
    admin_predictions.router, prefix="/admin", tags=["Admin — Predictions"]
)
api_v1_router.include_router(
    admin_current_affairs.router, prefix="/admin", tags=["Admin — Current Affairs"]
)
api_v1_router.include_router(
    admin_pattern_analytics.router, prefix="/admin", tags=["Admin — Pattern Analytics"]
)
api_v1_router.include_router(
    admin_dashboard.router, prefix="/admin", tags=["Admin — Dashboard"]
)
api_v1_router.include_router(
    payments.router, prefix="/payments", tags=["Payments"]
)
api_v1_router.include_router(
    email.router, tags=["Email Preferences"]
)
api_v1_router.include_router(
    admin_email.router, prefix="/admin", tags=["Admin — Email"]
)
