"""
PPSC Crack — Supabase Client
==============================
Singleton async Supabase client for Auth operations.

Two clients are provided:
- ``supabase``     — uses the **anon** key (client-facing operations)
- ``supabase_admin`` — uses the **service-role** key (server-side admin ops)

Both are lazy-initialised on first access via ``get_supabase()`` /
``get_supabase_admin()`` FastAPI dependencies, or directly via the
module-level variables after ``init_supabase()`` is called.
"""

from supabase import create_client, Client

from app.config import settings

# ── Module-level clients (initialised at startup) ───────────
supabase: Client | None = None
supabase_admin: Client | None = None


def init_supabase() -> tuple[Client, Client]:
    """Create and cache both Supabase clients.

    Called once during FastAPI lifespan startup.
    """
    global supabase, supabase_admin

    supabase = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY,
    )

    supabase_admin = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
    )

    return supabase, supabase_admin


def get_supabase() -> Client:
    """Return the anon-key Supabase client."""
    if supabase is None:
        init_supabase()
    assert supabase is not None
    return supabase


def get_supabase_admin() -> Client:
    """Return the service-role Supabase client (admin ops)."""
    if supabase_admin is None:
        init_supabase()
    assert supabase_admin is not None
    return supabase_admin
