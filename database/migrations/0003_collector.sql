-- MVP2: collection pipeline tables + provenance metadata (04, 12).

-- Governance metadata on spots (12_DATA_GOVERNANCE.md)
ALTER TABLE spots ADD COLUMN IF NOT EXISTS content_hash TEXT;
ALTER TABLE spots ADD COLUMN IF NOT EXISTS collected_at  TIMESTAMPTZ;
ALTER TABLE spots ADD COLUMN IF NOT EXISTS published_at  TIMESTAMPTZ;
ALTER TABLE spots ADD COLUMN IF NOT EXISTS license_note  TEXT;
ALTER TABLE spots ADD COLUMN IF NOT EXISTS data_class    CHAR(1);  -- A/B/C/D (12)
ALTER TABLE spots ADD COLUMN IF NOT EXISTS source_key    TEXT;
ALTER TABLE spots ADD COLUMN IF NOT EXISTS external_id   TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS uq_spots_content_hash
    ON spots (content_hash) WHERE content_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_spots_source_external
    ON spots (source_key, external_id);

-- Raw items: metadata + hash of what was fetched (04: Raw Data)
CREATE TABLE IF NOT EXISTS raw_items (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id    UUID REFERENCES sources(id) ON DELETE SET NULL,
    source_key   TEXT NOT NULL,
    external_id  TEXT,
    url          TEXT,
    title        TEXT,
    content_hash TEXT NOT NULL,
    payload      JSONB,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed    BOOLEAN NOT NULL DEFAULT false,
    UNIQUE (content_hash)
);
CREATE INDEX IF NOT EXISTS idx_raw_items_source ON raw_items (source_key, external_id);

-- Collector runs (04: 日次ジョブ / logs)
CREATE TABLE IF NOT EXISTS collector_runs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id    UUID REFERENCES sources(id) ON DELETE SET NULL,
    source_key   TEXT NOT NULL,
    started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at  TIMESTAMPTZ,
    status       TEXT NOT NULL DEFAULT 'running',  -- running / success / failed
    fetched      INTEGER NOT NULL DEFAULT 0,
    inserted     INTEGER NOT NULL DEFAULT 0,
    skipped      INTEGER NOT NULL DEFAULT 0,
    error_count  INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_collector_runs_started ON collector_runs (started_at DESC);

-- Collection errors (04: エラー処理を個別に記録)
CREATE TABLE IF NOT EXISTS collection_errors (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id     UUID REFERENCES collector_runs(id) ON DELETE CASCADE,
    source_key TEXT,
    error_type TEXT NOT NULL,   -- http / timeout / rate_limit / parse / validation / db
    message    TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_collection_errors_run ON collection_errors (run_id);
