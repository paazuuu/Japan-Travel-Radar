-- Feature C (Stage 9 foundation): user accounts + server-side saves.

CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name  TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_favorites (
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    spot_id    UUID NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, spot_id)
);

-- Attach saved plans to a user (nullable: anonymous plans still work).
ALTER TABLE travel_plans ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_travel_plans_user ON travel_plans (user_id);
