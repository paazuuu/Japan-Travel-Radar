-- MVP2 update feature: re-collection refresh, override lock, deletion detection.

-- Protect human-edited spots from being overwritten by the collector (05/12).
ALTER TABLE spots ADD COLUMN IF NOT EXISTS locked BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE spots ADD COLUMN IF NOT EXISTS last_collected_at TIMESTAMPTZ;

-- De-duplicate any pre-existing rows that share (source_key, external_id),
-- keeping the newest, so the unique index below can be created.
DELETE FROM spots a USING spots b
 WHERE a.source_key IS NOT NULL AND a.external_id IS NOT NULL
   AND a.source_key = b.source_key AND a.external_id = b.external_id
   AND a.ctid < b.ctid;

-- Stable per-source identity -> lets re-collection UPDATE the same row.
CREATE UNIQUE INDEX IF NOT EXISTS uq_spots_source_external_id
    ON spots (source_key, external_id)
    WHERE source_key IS NOT NULL AND external_id IS NOT NULL;

-- Track updates/pruned counts per collector run.
ALTER TABLE collector_runs ADD COLUMN IF NOT EXISTS updated INTEGER NOT NULL DEFAULT 0;
ALTER TABLE collector_runs ADD COLUMN IF NOT EXISTS pruned  INTEGER NOT NULL DEFAULT 0;
