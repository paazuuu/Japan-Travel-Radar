-- MVP3: AI analysis output, kept separate from source data (05, 12).

-- Distinguish AI-generated tags from manual/source tags.
ALTER TABLE spot_tags ADD COLUMN IF NOT EXISTS origin     TEXT NOT NULL DEFAULT 'manual';  -- manual / ai
ALTER TABLE spot_tags ADD COLUMN IF NOT EXISTS confidence NUMERIC(4,3);

-- One analysis row per spot. Structured output (05: JSON Schema固定).
CREATE TABLE IF NOT EXISTS spot_analyses (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spot_id      UUID NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
    summary      TEXT,
    categories   JSONB NOT NULL DEFAULT '[]',
    tags         JSONB NOT NULL DEFAULT '[]',
    best_season  JSONB NOT NULL DEFAULT '[]',
    travel_types JSONB NOT NULL DEFAULT '[]',
    food_tags    JSONB NOT NULL DEFAULT '[]',
    confidence   NUMERIC(4,3) NOT NULL DEFAULT 0,
    evidence     TEXT,                        -- 12: AI推定の根拠
    model        TEXT NOT NULL,               -- 'rule-based/v1' or LLM id
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed     BOOLEAN NOT NULL DEFAULT false,  -- human override applied
    override     JSONB,                       -- human corrections (05: 人間による修正)
    UNIQUE (spot_id)
);

CREATE INDEX IF NOT EXISTS idx_spot_analyses_spot ON spot_analyses (spot_id);
CREATE INDEX IF NOT EXISTS idx_spot_analyses_conf ON spot_analyses (confidence);
