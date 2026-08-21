-- Feature A: collect restaurants (provenance + update key), like spots.

ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS description  TEXT;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS subcategory  TEXT;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS content_hash TEXT;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS collected_at TIMESTAMPTZ;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS license_note TEXT;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS data_class   CHAR(1);
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS source_key   TEXT;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS external_id  TEXT;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS locked       BOOLEAN NOT NULL DEFAULT false;

CREATE UNIQUE INDEX IF NOT EXISTS uq_restaurants_source_external
    ON restaurants (source_key, external_id)
    WHERE source_key IS NOT NULL AND external_id IS NOT NULL;
