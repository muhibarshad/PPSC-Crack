"""
PPSC Crack — Application Settings
===================================
Loads configuration from environment variables / .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration pulled from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── App ──────────────────────────────────
    APP_NAME: str = "PPSC Crack"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # ── Server ───────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database (PostgreSQL 16 + pgvector) ──
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ppsc_crack"

    # ── Redis ────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Auth / JWT ───────────────────────────
    SECRET_KEY: str = "change-me-to-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ─────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # ── External APIs ────────────────────────
    OPENAI_API_KEY: str = ""


settings = Settings()
