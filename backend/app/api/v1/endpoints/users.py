"""
Users endpoints — CRUD operations.
"""

from fastapi import APIRouter, Depends

from app.dependencies import DBSession, get_current_user

router = APIRouter()


@router.get("/")
async def list_users(db: DBSession, current_user=Depends(get_current_user)):
    """List all users (admin only — add role check)."""
    # TODO: Implement with real DB query
    return {"users": [], "total": 0}


@router.get("/{user_id}")
async def get_user(user_id: int, db: DBSession, current_user=Depends(get_current_user)):
    """Get a specific user by ID."""
    # TODO: Implement with real DB query
    return {"id": user_id, "email": "placeholder@ppsccrack.pk"}


@router.put("/{user_id}")
async def update_user(user_id: int, db: DBSession, current_user=Depends(get_current_user)):
    """Update user profile."""
    # TODO: Implement
    return {"id": user_id, "message": "User updated"}


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: DBSession, current_user=Depends(get_current_user)):
    """Delete a user account."""
    # TODO: Implement
    return {"message": f"User {user_id} deleted"}
