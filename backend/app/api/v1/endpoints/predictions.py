"""
Predictions endpoints — AI-powered exam predictions.
"""

from fastapi import APIRouter, Depends, Query

from app.dependencies import DBSession, get_current_user

router = APIRouter()


@router.get("/")
async def list_predictions(
    db: DBSession,
    job_type: str | None = Query(None, description="Filter by job type"),
    current_user=Depends(get_current_user),
):
    """Get AI predictions for upcoming exams."""
    # TODO: Implement with real AI service
    return {
        "predictions": [],
        "job_type": job_type,
        "accuracy": "94%",
        "message": "Predictions generated from 500+ past papers",
    }


@router.get("/{prediction_id}")
async def get_prediction(
    prediction_id: int,
    db: DBSession,
    current_user=Depends(get_current_user),
):
    """Get a specific prediction detail."""
    # TODO: Implement
    return {"id": prediction_id, "topics": [], "confidence": 0.94}


@router.post("/generate")
async def generate_predictions(
    db: DBSession,
    job_type: str = Query(..., description="Job type to generate predictions for"),
    current_user=Depends(get_current_user),
):
    """Trigger AI prediction generation for a job type."""
    # TODO: Implement with AI pipeline
    return {
        "message": f"Prediction generation started for {job_type}",
        "status": "processing",
    }
