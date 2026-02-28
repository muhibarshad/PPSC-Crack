"""
Health-check endpoint.
"""

from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    """Return API health status."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
