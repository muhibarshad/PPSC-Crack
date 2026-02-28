-- ──────────────────────────────────────────────────────────
-- PPSC Crack — Database Initialization
-- ──────────────────────────────────────────────────────────
-- This script runs automatically on first container start
-- via /docker-entrypoint-initdb.d/
-- ──────────────────────────────────────────────────────────

-- 1. Install pgvector extension for embedding storage
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Install useful built-in extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS "pg_trgm";         -- trigram similarity (fuzzy search)
CREATE EXTENSION IF NOT EXISTS "unaccent";        -- accent-insensitive search

-- 3. Verify pgvector is installed
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE NOTICE '✅  pgvector extension installed successfully';
    ELSE
        RAISE EXCEPTION '❌  pgvector extension failed to install';
    END IF;
END
$$;

-- 4. Create application schema (optional — keeps things tidy)
CREATE SCHEMA IF NOT EXISTS app;

-- 5. Grant permissions
GRANT ALL ON SCHEMA app TO postgres;
GRANT ALL ON SCHEMA public TO postgres;
