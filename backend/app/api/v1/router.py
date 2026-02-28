"""
PPSC Crack — API v1 Aggregated Router
=======================================
Mounts all v1 endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    health,
    job_types,
    users,
    papers,
    predictions,
    current_affairs,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, prefix="/health", tags=["Health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_v1_router.include_router(job_types.router, prefix="/job-types", tags=["Job Types"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(papers.router, prefix="/papers", tags=["Papers"])
api_v1_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
api_v1_router.include_router(
    current_affairs.router, prefix="/current-affairs", tags=["Current Affairs"]
)
