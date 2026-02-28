"""
Current Affairs endpoints — daily news pipeline.
"""

from fastapi import APIRouter, Depends, Query

from app.dependencies import DBSession, get_current_user

router = APIRouter()


@router.get("/")
async def list_current_affairs(
    db: DBSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: str | None = Query(None, description="Filter by category"),
):
    """List current affairs articles."""
    # TODO: Implement with real DB query
    return {"articles": [], "total": 0, "page": page, "per_page": per_page}


@router.get("/{article_id}")
async def get_article(article_id: int, db: DBSession):
    """Get a specific current affairs article."""
    # TODO: Implement
    return {"id": article_id, "title": "Placeholder Article"}


@router.post("/")
async def create_article(db: DBSession, current_user=Depends(get_current_user)):
    """Create a new current affairs article (admin)."""
    # TODO: Implement
    return {"message": "Article created"}
