"""
PPSC Crack — FastAPI Application Factory
=========================================
Entry point for the backend server.
Run with:  uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.api.v1.router import api_v1_router
from app.core.supabase_client import init_supabase
from app.database import engine, Base, redis_pool

logger = logging.getLogger(__name__)


# ── Lifespan ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown logic."""
    # Startup: create tables (dev only — use Alembic in production)
    async with engine.begin() as conn:
        # Ensure pgvector extension exists
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    # Verify Redis connectivity
    await redis_pool.ping()

    # Initialise Supabase clients (anon + admin)
    init_supabase()

    yield

    # Shutdown: close connections
    await redis_pool.aclose()
    await engine.dispose()


# ── App Instance ────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="PPSC Crack — AI-Powered Exam Domination System API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Exception Handler ────────────────────────────────
@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all so the frontend always receives JSON, never a bare 500."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


# ── Routers ─────────────────────────────────────────────────
app.include_router(api_v1_router, prefix="/api/v1")

# Shortcut: mount auth endpoints at /api/auth as well (user-facing path)
from app.api.v1.endpoints.auth import router as auth_router
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])


# ── Root ────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
