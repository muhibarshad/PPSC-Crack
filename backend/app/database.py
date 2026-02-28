"""PPSC Crack — Database Engine & Session Manager
==================================================
Async SQLAlchemy 2.x setup with PostgreSQL 16 (asyncpg) + pgvector.
Redis async connection pool for caching / rate-limiting.

Usage
-----
FastAPI dependency injection (recommended)::

    from app.database import get_db
    async def my_endpoint(db: AsyncSession = Depends(get_db)):
        ...

Standalone (scripts, tests, background tasks)::

    from app.database import SessionManager
    async with SessionManager() as db:
        result = await db.execute(select(User))
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from pgvector.sqlalchemy import Vector  # noqa: F401  — re-exported for models
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# ═══════════════════════════════════════════════════════════
# PostgreSQL — Async Engine (asyncpg driver)
# ═══════════════════════════════════════════════════════════
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    # ── Connection Pool ──────────────────────
    pool_pre_ping=True,          # detect stale connections
    pool_size=20,                # maintained idle connections
    max_overflow=10,             # extra connections on burst
    pool_timeout=30,             # seconds to wait for a conn
    pool_recycle=1800,           # recycle connections every 30 min
    # ── asyncpg connect_args ────────────────
    connect_args={
        "server_settings": {
            "jit": "off",                         # faster planning for short queries
            "application_name": "ppsc_crack_api",
        },
        "command_timeout": 60,
    },
)

# ── Session Factory ─────────────────────────────────────────
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ═══════════════════════════════════════════════════════════
# Declarative Base
# ═══════════════════════════════════════════════════════════
class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


# ═══════════════════════════════════════════════════════════
# Redis — Async Connection Pool
# ═══════════════════════════════════════════════════════════
redis_pool: aioredis.Redis = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
    max_connections=20,
)


# ═══════════════════════════════════════════════════════════
# Session Manager — standalone async context manager
# ═══════════════════════════════════════════════════════════
class SessionManager:
    """Async context-manager that auto-commits / rolls back.

    Useful for scripts, tests, and background workers that run
    outside the FastAPI request lifecycle::

        async with SessionManager() as db:
            user = await db.get(User, some_uuid)
    """

    def __init__(self, auto_commit: bool = True) -> None:
        self._auto_commit = auto_commit
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        self._session = async_session()
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[override]
        assert self._session is not None
        try:
            if exc_type is not None:
                await self._session.rollback()
            elif self._auto_commit:
                await self._session.commit()
        finally:
            await self._session.close()
            self._session = None


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Functional shortcut — ``async with get_session() as db:``."""
    async with SessionManager() as db:
        yield db


# ═══════════════════════════════════════════════════════════
# FastAPI Dependencies
# ═══════════════════════════════════════════════════════════
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a DB session per request, with auto-rollback on error."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Yield the shared Redis connection pool."""
    yield redis_pool
