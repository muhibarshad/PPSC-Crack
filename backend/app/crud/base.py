"""
Generic async CRUD base class for SQLAlchemy 2.x models.
==========================================================
Provides reusable **create / read / update / delete / list** operations
that every model-specific CRUD module inherits.

Usage::

    from app.crud.base import CRUDBase
    from app.models.user import User
    from app.schemas.user import UserCreate, UserUpdate

    class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
        pass

    crud_user = CRUDUser(User)
"""

from typing import Any, Generic, Sequence, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func, select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

# Type variables for the ORM model and Pydantic schemas
ModelT = TypeVar("ModelT", bound=Base)
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)


class CRUDBase(Generic[ModelT, CreateSchemaT, UpdateSchemaT]):
    """Async CRUD helper with pagination, filtering, and bulk ops."""

    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    # ── READ ─────────────────────────────────────────────────

    async def get(self, db: AsyncSession, *, id: UUID) -> ModelT | None:
        """Get a single record by primary key."""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_or_404(self, db: AsyncSession, *, id: UUID) -> ModelT:
        """Get a single record or raise 404."""
        from app.core.exceptions import NotFound

        obj = await self.get(db, id=id)
        if obj is None:
            raise NotFound(f"{self.model.__name__} with id={id} not found")
        return obj

    async def get_by_field(
        self, db: AsyncSession, *, field: str, value: Any
    ) -> ModelT | None:
        """Get a single record by an arbitrary column value."""
        col = getattr(self.model, field)
        result = await db.execute(select(self.model).where(col == value))
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        descending: bool = True,
        filters: dict[str, Any] | None = None,
    ) -> tuple[Sequence[ModelT], int]:
        """Return a paginated list + total count.

        Parameters
        ----------
        skip : int
            Offset (0-based).
        limit : int
            Max rows to return.
        order_by : str | None
            Column name to sort by. Defaults to ``created_at`` if the
            model has it, otherwise the primary key.
        descending : bool
            Sort direction (default newest first).
        filters : dict
            ``{column_name: value}`` equality filters.

        Returns
        -------
        tuple[list[ModelT], int]
            (rows, total_count)
        """
        query = select(self.model)
        count_query = select(func.count()).select_from(self.model)

        # Apply equality filters
        if filters:
            for col_name, val in filters.items():
                col = getattr(self.model, col_name, None)
                if col is not None and val is not None:
                    query = query.where(col == val)
                    count_query = count_query.where(col == val)

        # Count
        total: int = (await db.execute(count_query)).scalar() or 0

        # Ordering
        if order_by and hasattr(self.model, order_by):
            col = getattr(self.model, order_by)
        elif hasattr(self.model, "created_at"):
            col = self.model.created_at
        else:
            col = self.model.id

        query = query.order_by(col.desc() if descending else col.asc())

        # Pagination
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all(), total

    # ── CREATE ───────────────────────────────────────────────

    async def create(
        self, db: AsyncSession, *, obj_in: CreateSchemaT
    ) -> ModelT:
        """Insert a new row from a Pydantic create schema."""
        data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(**data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def create_many(
        self, db: AsyncSession, *, objs_in: list[CreateSchemaT]
    ) -> list[ModelT]:
        """Bulk-insert multiple rows."""
        db_objs = [self.model(**o.model_dump(exclude_unset=True)) for o in objs_in]
        db.add_all(db_objs)
        await db.flush()
        for obj in db_objs:
            await db.refresh(obj)
        return db_objs

    # ── UPDATE ───────────────────────────────────────────────

    async def update(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        obj_in: UpdateSchemaT | dict[str, Any],
    ) -> ModelT:
        """Partial-update a record.  Accepts a Pydantic schema or a dict."""
        db_obj = await self.get_or_404(db, id=id)

        update_data: dict[str, Any]
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    # ── DELETE ───────────────────────────────────────────────

    async def delete(self, db: AsyncSession, *, id: UUID) -> ModelT:
        """Delete a record by PK; returns the deleted object."""
        db_obj = await self.get_or_404(db, id=id)
        await db.delete(db_obj)
        await db.flush()
        return db_obj

    async def delete_many(self, db: AsyncSession, *, ids: list[UUID]) -> int:
        """Bulk-delete by a list of IDs. Returns count deleted."""
        stmt = sa_delete(self.model).where(self.model.id.in_(ids))
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount  # type: ignore[return-value]

    # ── HELPERS ──────────────────────────────────────────────

    async def count(
        self, db: AsyncSession, *, filters: dict[str, Any] | None = None
    ) -> int:
        """Count rows with optional filters."""
        query = select(func.count()).select_from(self.model)
        if filters:
            for col_name, val in filters.items():
                col = getattr(self.model, col_name, None)
                if col is not None and val is not None:
                    query = query.where(col == val)
        return (await db.execute(query)).scalar() or 0

    async def exists(self, db: AsyncSession, *, id: UUID) -> bool:
        """Check if a record exists."""
        query = select(func.count()).select_from(self.model).where(self.model.id == id)
        return ((await db.execute(query)).scalar() or 0) > 0
