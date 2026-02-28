"""
Papers endpoints — past paper management.
"""

from fastapi import APIRouter, Depends, Query

from app.dependencies import DBSession, get_current_user
from app.schemas.paper import PaperListResponse

router = APIRouter()

# ── Mock data matching frontend JOB_TYPES ───────────────────
JOB_TYPES = [
    {"id": "clerk",       "label": "Clerk",          "papers_count": 120},
    {"id": "asi",         "label": "ASI",            "papers_count": 85},
    {"id": "tehsildar",   "label": "Tehsildar",      "papers_count": 64},
    {"id": "teacher",     "label": "Teacher",        "papers_count": 97},
    {"id": "inspector",   "label": "Inspector",      "papers_count": 58},
    {"id": "naib-tehsil", "label": "Naib Tehsildar", "papers_count": 43},
]


@router.get("/job-types")
async def list_job_types():
    """List available job types with paper counts."""
    return {"job_types": JOB_TYPES}


@router.get("/", response_model=PaperListResponse)
async def list_papers(
    db: DBSession,
    job_type: str | None = Query(None, description="Filter by job type"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List past papers with optional filtering."""
    # TODO: Implement with real DB query
    return PaperListResponse(papers=[], total=0, page=page, per_page=per_page)


@router.get("/{paper_id}")
async def get_paper(paper_id: int, db: DBSession):
    """Get a specific past paper with its questions."""
    # TODO: Implement
    return {"id": paper_id, "title": "Placeholder Paper"}


@router.post("/")
async def create_paper(db: DBSession, current_user=Depends(get_current_user)):
    """Upload a new past paper (admin)."""
    # TODO: Implement
    return {"message": "Paper created"}
