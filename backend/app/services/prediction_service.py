"""
Prediction service — AI prediction management.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction
from app.core.exceptions import NotFound


async def get_predictions_by_job(db: AsyncSession, job_type: str) -> list[Prediction]:
    """Return predictions for a specific job type."""
    result = await db.execute(
        select(Prediction)
        .where(Prediction.job_type == job_type)
        .order_by(Prediction.generated_at.desc())
    )
    return list(result.scalars().all())


async def get_prediction_by_id(db: AsyncSession, prediction_id: int) -> Prediction:
    """Fetch a single prediction."""
    result = await db.execute(select(Prediction).where(Prediction.id == prediction_id))
    prediction = result.scalar_one_or_none()
    if not prediction:
        raise NotFound(f"Prediction {prediction_id} not found")
    return prediction
