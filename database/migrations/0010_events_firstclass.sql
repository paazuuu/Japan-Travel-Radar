-- Feature A: make events first-class (collected into the events table).

ALTER TABLE events ADD COLUMN IF NOT EXISTS description  TEXT;
ALTER TABLE events ADD COLUMN IF NOT EXISTS subcategory  TEXT;
ALTER TABLE events ADD COLUMN IF NOT EXISTS content_hash TEXT;
ALTER TABLE events ADD COLUMN IF NOT EXISTS collected_at TIMESTAMPTZ;
ALTER TABLE events ADD COLUMN IF NOT EXISTS license_note TEXT;
ALTER TABLE events ADD COLUMN IF NOT EXISTS data_class   CHAR(1);
ALTER TABLE events ADD COLUMN IF NOT EXISTS source_key   TEXT;
ALTER TABLE events ADD COLUMN IF NOT EXISTS external_id  TEXT;
ALTER TABLE events ADD COLUMN IF NOT EXISTS locked       BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE events ADD COLUMN IF NOT EXISTS status       TEXT NOT NULL DEFAULT 'published';

CREATE UNIQUE INDEX IF NOT EXISTS uq_events_source_external
    ON events (source_key, external_id)
    WHERE source_key IS NOT NULL AND external_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_events_prefecture ON events (prefecture_id);
