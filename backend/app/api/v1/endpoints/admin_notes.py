"""
Admin Notes Endpoints
========================
POST   /api/v1/admin/notes       — upload raw note content → queue AI processing
GET    /api/v1/admin/notes       — list all notes with topic assignments + status
GET    /api/v1/admin/notes/{id}  — get a single note's full details
DELETE /api/v1/admin/notes/{id}  — delete a note
POST   /api/v1/admin/notes/batch — trigger batch processing of all unprocessed notes
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DBSession, require_admin
from app.crud.crud_admin_note import crud_admin_note
from app.models.admin_note import AdminNote
from app.models.topic import Topic
from app.models.user import User
from app.schemas.admin_note import (
    AdminNoteCreate,
    AdminNoteListResponse,
    AdminNoteResponse,
    AdminNoteUploadResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────

def _build_response(note: AdminNote) -> AdminNoteResponse:
    """Map AdminNote ORM → AdminNoteResponse with topic info."""
    topic = note.topic_rel
    return AdminNoteResponse(
        id=note.id,
        raw_content=note.raw_content,
        source_description=note.source_description,
        processed=note.processed,
        assigned_topic_id=note.assigned_topic_id,
        processed_content=note.processed_content,
        position_in_story=note.position_in_story,
        created_at=note.created_at,
        topic_name=topic.name if topic else None,
        topic_display_name=topic.display_name if topic else None,
    )


# ── POST /notes ─────────────────────────────────────────────

@router.post(
    "/notes",
    response_model=AdminNoteUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload raw admin note content",
    description=(
        "Creates a new admin note and immediately queues it for AI processing. "
        "The pipeline identifies the topic, extracts facts, determines the story "
        "section, generates an embedding, and triggers an incremental story update."
    ),
)
async def upload_admin_note(
    payload: AdminNoteCreate,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Upload a raw admin note and trigger AI processing."""
    # Create the note
    note = await crud_admin_note.create(db, obj_in=payload)
    await db.commit()
    await db.refresh(note)

    # Queue background processing
    task_id: str | None = None
    try:
        from app.tasks.note_processing import trigger_note_processing
        task_id = trigger_note_processing(str(note.id))
    except Exception:
        logger.exception("Failed to queue processing for note %s", note.id)

    return AdminNoteUploadResponse(
        id=note.id,
        status="queued" if task_id else "created",
        task_id=task_id,
        message=(
            "Note uploaded and queued for AI processing"
            if task_id
            else "Note created but processing queue unavailable — will be picked up by batch"
        ),
    )


# ── GET /notes ──────────────────────────────────────────────

@router.get(
    "/notes",
    response_model=AdminNoteListResponse,
    summary="List all admin notes",
    description=(
        "Paginated list of all admin notes with topic assignments and "
        "processing status. Optionally filter by topic or processed status."
    ),
)
async def list_admin_notes(
    db: DBSession,
    admin: User = Depends(require_admin),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    topic_id: UUID | None = Query(None, description="Filter by assigned topic"),
    processed: bool | None = Query(None, description="Filter by processed status"),
):
    """List admin notes with optional filters."""
    # Build base query
    query = select(AdminNote).order_by(AdminNote.created_at.desc())

    if topic_id is not None:
        query = query.where(AdminNote.assigned_topic_id == topic_id)
    if processed is not None:
        query = query.where(AdminNote.processed == processed)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    result = await db.execute(query)
    notes = list(result.scalars().all())

    return AdminNoteListResponse(
        notes=[_build_response(n) for n in notes],
        total=total,
        page=page,
        per_page=per_page,
    )


# ── GET /notes/{id} ────────────────────────────────────────

@router.get(
    "/notes/{note_id}",
    response_model=AdminNoteResponse,
    summary="Get a single admin note",
)
async def get_admin_note(
    note_id: UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Get full details of a single admin note."""
    note = await crud_admin_note.get_or_404(db, id=note_id)
    return _build_response(note)


# ── DELETE /notes/{id} ──────────────────────────────────────

@router.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an admin note",
)
async def delete_admin_note(
    note_id: UUID,
    db: DBSession,
    admin: User = Depends(require_admin),
):
    """Delete an admin note."""
    await crud_admin_note.get_or_404(db, id=note_id)
    await crud_admin_note.delete(db, id=note_id)
    await db.commit()
    return None


# ── POST /notes/batch ───────────────────────────────────────

@router.post(
    "/notes/batch-process",
    summary="Trigger batch processing of all unprocessed notes",
    description=(
        "Enqueues a Celery task that processes all admin notes with "
        "``processed=False``. Returns the task ID for status polling."
    ),
)
async def batch_process_notes(
    db: DBSession,
    admin: User = Depends(require_admin),
    limit: int = Query(50, ge=1, le=200, description="Max notes to process"),
):
    """Trigger batch processing of unprocessed admin notes."""
    # Check how many unprocessed notes exist
    count_result = await db.execute(
        select(func.count())
        .select_from(AdminNote)
        .where(AdminNote.processed.is_(False))
    )
    pending = count_result.scalar() or 0

    if pending == 0:
        return {"status": "no_pending", "message": "All notes already processed", "pending": 0}

    try:
        from app.tasks.note_processing import batch_process_admin_notes
        task = batch_process_admin_notes.apply_async(
            kwargs={"limit": limit},
            queue="ai_pipeline",
        )
        return {
            "status": "queued",
            "task_id": task.id,
            "pending": pending,
            "message": f"Batch processing queued for up to {min(limit, pending)} notes",
        }
    except Exception:
        logger.exception("Failed to queue batch note processing")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task queue unavailable — try again later",
        )
