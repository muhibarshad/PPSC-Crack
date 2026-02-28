"""
Job Types API — Full CRUD for PPSC job categories.
=====================================================
Public:  GET list / detail (active only).
Admin:   POST, PUT, PATCH topic_ratios, DELETE.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.crud.crud_job_type import crud_job_type
from app.dependencies import DBSession, get_current_user, require_admin
from app.models.user import User
from app.schemas.job_type import (
    JobTypeCreate,
    JobTypeListResponse,
    JobTypeResponse,
    JobTypeUpdate,
    JobTypeTopicRatiosUpdate,
)

router = APIRouter()


# ═══════════════════════════════════════════════════════════
# PUBLIC — Anyone authenticated can read active job types
# ═══════════════════════════════════════════════════════════


@router.get(
    "/",
    response_model=JobTypeListResponse,
    summary="List job types",
)
async def list_job_types(
    db: DBSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = Query(True),
):
    """Return paginated job types. Public endpoint (no auth required)."""
    if active_only:
        items = await crud_job_type.get_active(db)
        return JobTypeListResponse(job_types=items, total=len(items))

    items, total = await crud_job_type.get_multi(
        db, skip=skip, limit=limit, order_by="name", descending=False,
    )
    return JobTypeListResponse(job_types=items, total=total)


@router.get(
    "/{job_type_id}",
    response_model=JobTypeResponse,
    summary="Get a single job type",
)
async def get_job_type(job_type_id: UUID, db: DBSession):
    """Fetch a job type by ID. Public endpoint."""
    return await crud_job_type.get_or_404(db, id=job_type_id)


@router.get(
    "/slug/{slug}",
    response_model=JobTypeResponse,
    summary="Get job type by slug",
)
async def get_job_type_by_slug(slug: str, db: DBSession):
    """Fetch a job type by its URL-safe slug."""
    from app.core.exceptions import NotFound

    obj = await crud_job_type.get_by_slug(db, slug=slug)
    if obj is None:
        raise NotFound(f"Job type with slug '{slug}' not found")
    return obj


# ═══════════════════════════════════════════════════════════
# ADMIN — Requires JWT + role='admin'
# ═══════════════════════════════════════════════════════════


@router.post(
    "/",
    response_model=JobTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a job type (admin)",
)
async def create_job_type(
    body: JobTypeCreate,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Create a new PPSC job type."""
    return await crud_job_type.create(db, obj_in=body)


@router.put(
    "/{job_type_id}",
    response_model=JobTypeResponse,
    summary="Update a job type (admin)",
)
async def update_job_type(
    job_type_id: UUID,
    body: JobTypeUpdate,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Update name, slug, department, or active status."""
    return await crud_job_type.update(db, id=job_type_id, obj_in=body)


@router.patch(
    "/{job_type_id}/topic-ratios",
    response_model=JobTypeResponse,
    summary="Set topic ratios JSONB (admin)",
)
async def set_topic_ratios(
    job_type_id: UUID,
    body: JobTypeTopicRatiosUpdate,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Manually override the topic_ratios JSON for a job type."""
    return await crud_job_type.update_topic_ratios(
        db, id=job_type_id, ratios=body.topic_ratios,
    )


@router.delete(
    "/{job_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job type (admin)",
)
async def delete_job_type(
    job_type_id: UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Permanently delete a job type."""
    await crud_job_type.delete(db, id=job_type_id)
    return None
