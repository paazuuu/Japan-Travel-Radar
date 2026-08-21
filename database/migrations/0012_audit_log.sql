-- Feature B: audit log for admin mutations (12: 管理操作の追跡).

CREATE TABLE IF NOT EXISTS audit_log (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action     TEXT NOT NULL,             -- e.g. 'spot.override', 'analysis.review'
    entity     TEXT,                      -- table / entity type
    entity_id  UUID,
    detail     JSONB,
    actor      TEXT,                      -- who (admin key id / user later)
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log (created_at DESC);
