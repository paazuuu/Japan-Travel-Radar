-- MVP6: travel plans (08_MVP6_TRAVEL_PLANNER.md, 17_DATA_MODEL_DETAIL.md).
-- Reproducible input conditions are stored so a plan can be regenerated/edited.

CREATE TABLE IF NOT EXISTS travel_plans (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origin       TEXT NOT NULL,
    origin_lat   DOUBLE PRECISION,
    origin_lng   DOUBLE PRECISION,
    start_date   DATE,
    days         INTEGER NOT NULL DEFAULT 1,
    budget       INTEGER,
    party_size   INTEGER NOT NULL DEFAULT 1,
    transport    TEXT NOT NULL DEFAULT 'train',   -- train / car / walk
    preferences  JSONB NOT NULL DEFAULT '{}',      -- purpose tags, food, etc (reproducible input)
    summary      TEXT,
    total_cost   INTEGER,
    within_budget BOOLEAN,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS travel_plan_items (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id        UUID NOT NULL REFERENCES travel_plans(id) ON DELETE CASCADE,
    sequence       INTEGER NOT NULL,
    kind           TEXT NOT NULL,                 -- depart / spot / meal / cafe / return
    spot_id        UUID REFERENCES spots(id) ON DELETE SET NULL,
    restaurant_id  UUID REFERENCES restaurants(id) ON DELETE SET NULL,
    label          TEXT NOT NULL,
    start_time     TEXT,                          -- 'HH:MM'
    end_time       TEXT,
    estimated_cost INTEGER NOT NULL DEFAULT 0,
    travel_time    INTEGER NOT NULL DEFAULT 0,     -- minutes to reach this item
    source_url     TEXT,
    UNIQUE (plan_id, sequence)
);

CREATE INDEX IF NOT EXISTS idx_plan_items_plan ON travel_plan_items (plan_id, sequence);
