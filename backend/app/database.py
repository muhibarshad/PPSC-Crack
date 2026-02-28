"""PPSC Crack — Database Engine & Session
========================================
Async SQLAlchemy 2.x setup with PostgreSQL 16 (asyncpg) + pgvector.
Redis async connection pool for caching / rate-limiting.
"""

from collections.abc import AsyncGenerator

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
        finally:
            await session.close()


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Yield a Redis connection per request."""
    yield redis_pool
