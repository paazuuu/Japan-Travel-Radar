-- MVP0: enable required PostgreSQL extensions.
-- Executed automatically on first container start via docker-entrypoint-initdb.d.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Sanity marker so `docker compose logs postgres` shows init ran.
DO $$
BEGIN
    RAISE NOTICE 'Japan Travel Radar: PostGIS % initialized', PostGIS_Version();
END $$;
