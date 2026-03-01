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

    # ── Supabase ───────────────────────────────
    SUPABASE_URL: str = "https://your-project.supabase.co"
    SUPABASE_ANON_KEY: str = "your-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "your-service-role-key"
    SUPABASE_JWT_SECRET: str = "your-jwt-secret"

    # ── Auth / JWT ───────────────────────────
    SECRET_KEY: str = "change-me-to-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Auth Rate Limiting ───────────────────
    AUTH_RATE_LIMIT_MAX: int = 10
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 900  # 15 minutes

    # ── Cookie Settings ──────────────────────
    COOKIE_DOMAIN: str | None = None
    COOKIE_SECURE: bool = False  # True in production (HTTPS)
    COOKIE_SAMESITE: str = "lax"

    # ── CORS ─────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # ── External APIs ────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_ORG_ID: str | None = None

    # ── OpenAI Model Defaults ────────────────
    OPENAI_MODEL_GPT4O: str = "gpt-4o"
    OPENAI_MODEL_GPT4O_MINI: str = "gpt-4o-mini"
    OPENAI_MODEL_EMBEDDING: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_DIMENSIONS: int = 1536

    # ── OpenAI Retry / Rate-Limit ────────────
    OPENAI_MAX_RETRIES: int = 5
    OPENAI_RETRY_BASE_DELAY: float = 1.0
    OPENAI_RETRY_MAX_DELAY: float = 60.0
    OPENAI_REQUEST_TIMEOUT: float = 120.0

    # ── Cost Tracking ────────────────────────
    OPENAI_COST_LOG_ENABLED: bool = True

    # ── Stripe Payments ───────────────────────
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_BASIC_MONTHLY_PRICE_ID: str = ""
    STRIPE_BASIC_ANNUAL_PRICE_ID: str = ""
    STRIPE_PRO_MONTHLY_PRICE_ID: str = ""
    STRIPE_PRO_ANNUAL_PRICE_ID: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    # ── JazzCash Payments ────────────────────
    JAZZCASH_MERCHANT_ID: str = ""
    JAZZCASH_PASSWORD: str = ""
    JAZZCASH_INTEGRITY_SALT: str = ""
    JAZZCASH_ENDPOINT: str = "https://sandbox.jazzcash.com.pk/ApplicationAPI/API/2.0/Purchase/DoMWalletTransaction"
    JAZZCASH_CHECKOUT_URL: str = "https://sandbox.jazzcash.com.pk/CustomerPortal/transactionmanagement/merchantform"
    JAZZCASH_RETURN_URL: str = "http://localhost:3000/dashboard/subscription"

    # ── Object Storage (S3 / Cloudflare R2) ──
    STORAGE_BACKEND: str = "s3"  # "s3" or "r2" or "local"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "ppsc-crack-scans"
    S3_ENDPOINT_URL: str | None = None  # Set for R2: https://<account>.r2.cloudflarestorage.com
    S3_PUBLIC_URL_PREFIX: str = ""  # CDN prefix for public URLs, e.g. https://cdn.ppsc-crack.pk/scans

    # ── Scan OCR ─────────────────────────────
    OCR_CONFIDENCE_THRESHOLD: float = 0.85
    OCR_MAX_IMAGES: int = 4
    SCAN_MAX_FILE_SIZE_MB: int = 10

    # ── Resend (Transactional Email) ─────────
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "PPSC Crack <noreply@ppsc-crack.pk>"
    RESEND_REPLY_TO: str = "support@ppsc-crack.pk"


settings = Settings()
