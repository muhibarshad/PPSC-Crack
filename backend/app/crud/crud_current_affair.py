"""CRUD helpers for **CurrentAffairsItem** model.

Includes pgvector similarity search, date-based queries for student/admin
feeds, and admin approval workflow.
"""

from typing import Any, Sequence
from uuid import UUID
from datetime import date, timedelta

from sqlalchemy import select, func, text as sa_text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.current_affair import CurrentAffairsItem
from app.schemas.current_affair import CurrentAffairCreate, CurrentAffairUpdate


class CRUDCurrentAffair(CRUDBase[CurrentAffairsItem, CurrentAffairCreate, CurrentAffairUpdate]):
    """Extended CRUD for current_affairs_items table."""

    # ── Student Feed: today's approved articles ──────────────

    async def get_student_feed(
        self,
        db: AsyncSession,
        *,
        target_date: date | None = None,
        category: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[CurrentAffairsItem], int]:
        """Return today's (or specified date's) approved articles for students.

        Only articles with is_approved=True are returned.
        Falls back to last 7 days if no articles exist for the target date.
        """
        target = target_date or date.today()
        fallback_start = target - timedelta(days=7)

        conditions = [
            self.model.is_approved.is_(True),
            or_(
                self.model.published_date == target,
                and_(
                    self.model.published_date >= fallback_start,
                    self.model.published_date <= target,
                ),
            ),
        ]

        if category:
            conditions.append(self.model.category == category)

        base = select(self.model).where(and_(*conditions))
        count_q = select(func.count()).select_from(self.model).where(and_(*conditions))

        total: int = (await db.execute(count_q)).scalar() or 0
        result = await db.execute(
            base.order_by(
                self.model.relevance_score.desc(),
                self.model.published_date.desc().nullslast(),
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all(), total

    # ── Admin Feed: all articles with full scoring details ───

    async def get_admin_feed(
        self,
        db: AsyncSession,
        *,
        target_date: date | None = None,
        category: str | None = None,
        source_name: str | None = None,
        is_approved: bool | None = None,
        min_relevance: float | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[CurrentAffairsItem], int]:
        """Return articles for admin view with full scoring and filter options."""
        conditions = []

        if target_date:
            conditions.append(self.model.published_date == target_date)
        if category:
            conditions.append(self.model.category == category)
        if source_name:
            conditions.append(self.model.source_name == source_name)
        if is_approved is not None:
            conditions.append(self.model.is_approved.is_(is_approved))
        if min_relevance is not None:
            conditions.append(self.model.relevance_score >= min_relevance)

        where_clause = and_(*conditions) if conditions else True

        base = select(self.model).where(where_clause)
        count_q = select(func.count()).select_from(self.model).where(where_clause)

        total: int = (await db.execute(count_q)).scalar() or 0
        result = await db.execute(
            base.order_by(self.model.relevance_score.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all(), total

    # ── Approve / reject ─────────────────────────────────────

    async def approve(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        is_approved: bool = True,
        is_included_in_prediction: bool = False,
        approved_by: UUID | None = None,
    ) -> CurrentAffairsItem:
        """Approve or reject a current affairs item."""
        from datetime import datetime, timezone

        obj = await self.get_or_404(db, id=id)
        obj.is_approved = is_approved
        obj.is_included_in_prediction = is_included_in_prediction
        if is_approved and approved_by:
            obj.approved_by = approved_by
            obj.approved_at = datetime.now(timezone.utc)
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    # ── Category-based queries ───────────────────────────────

    async def get_by_category(
        self,
        db: AsyncSession,
        *,
        category: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[CurrentAffairsItem], int]:
        """List items by category with count."""
        base = select(self.model).where(self.model.category == category)
        count_q = select(func.count()).select_from(self.model).where(
            self.model.category == category
        )

        total: int = (await db.execute(count_q)).scalar() or 0
        result = await db.execute(
            base.order_by(self.model.published_date.desc().nullslast())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def get_exam_relevant(
        self,
        db: AsyncSession,
        *,
        min_relevance: float = 0.7,
        limit: int = 50,
    ) -> list[CurrentAffairsItem]:
        """Return items above a relevance threshold."""
        result = await db.execute(
            select(self.model)
            .where(self.model.relevance_score >= min_relevance)
            .order_by(self.model.relevance_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_for_prediction(
        self, db: AsyncSession, *, limit: int = 100
    ) -> list[CurrentAffairsItem]:
        """Return items flagged for inclusion in predictions."""
        result = await db.execute(
            select(self.model)
            .where(self.model.is_included_in_prediction.is_(True))
            .order_by(self.model.published_date.desc().nullslast())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_without_mcq(
        self, db: AsyncSession, *, limit: int = 50
    ) -> list[CurrentAffairsItem]:
        """Return items that haven't had MCQs generated yet."""
        result = await db.execute(
            select(self.model)
            .where(self.model.mcq_generated.is_(False))
            .where(self.model.relevance_score >= 0.65)
            .order_by(self.model.relevance_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Check URL exists (dedup) ─────────────────────────────

    async def url_exists(self, db: AsyncSession, *, url: str) -> bool:
        """Check if a source_url already exists in the DB."""
        result = await db.execute(
            select(func.count()).select_from(self.model).where(
                self.model.source_url == url
            )
        )
        return (result.scalar() or 0) > 0

    # ── pgvector similarity search ───────────────────────────

    async def find_similar(
        self,
        db: AsyncSession,
        *,
        embedding: list[float],
        limit: int = 10,
        threshold: float = 0.80,
    ) -> list[dict[str, Any]]:
        """Cosine similarity search on current affairs embeddings."""
        vec_literal = f"[{','.join(str(v) for v in embedding)}]"

        stmt = (
            select(
                self.model,
                sa_text(f"1 - (embedding <=> '{vec_literal}'::vector) AS similarity"),
            )
            .where(self.model.embedding.isnot(None))
            .order_by(sa_text(f"embedding <=> '{vec_literal}'::vector"))
            .limit(limit)
        )

        result = await db.execute(stmt)
        rows = result.all()

        return [
            {"item": row[0], "similarity_score": float(row[1])}
            for row in rows
            if float(row[1]) >= threshold
        ]

    async def set_embedding(
        self, db: AsyncSession, *, id: UUID, embedding: list[float]
    ) -> CurrentAffairsItem:
        """Store the embedding vector for an item."""
        obj = await self.get_or_404(db, id=id)
        obj.embedding = embedding  # type: ignore[assignment]
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    # ── Daily stats ──────────────────────────────────────────

    async def get_daily_stats(
        self, db: AsyncSession, *, target_date: date | None = None
    ) -> dict[str, Any]:
        """Return aggregate stats for a given date."""
        target = target_date or date.today()

        total_q = select(func.count()).select_from(self.model).where(
            self.model.published_date == target
        )
        approved_q = select(func.count()).select_from(self.model).where(
            and_(self.model.published_date == target, self.model.is_approved.is_(True))
        )
        mcq_q = select(func.count()).select_from(self.model).where(
            and_(self.model.published_date == target, self.model.mcq_generated.is_(True))
        )
        avg_score_q = select(func.avg(self.model.relevance_score)).where(
            self.model.published_date == target
        )

        total = (await db.execute(total_q)).scalar() or 0
        approved = (await db.execute(approved_q)).scalar() or 0
        mcqs = (await db.execute(mcq_q)).scalar() or 0
        avg_score = (await db.execute(avg_score_q)).scalar() or 0.0

        return {
            "date": str(target),
            "total_articles": total,
            "approved_articles": approved,
            "mcqs_generated": mcqs,
            "avg_relevance_score": round(float(avg_score), 4),
        }


crud_current_affair = CRUDCurrentAffair(CurrentAffairsItem)
