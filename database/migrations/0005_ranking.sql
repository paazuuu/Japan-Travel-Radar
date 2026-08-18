-- MVP4: trend / ranking (06_MVP4_RANKING.md, 17_DATA_MODEL_DETAIL.md).

-- Time-series observations to compute growth (17: observations)
CREATE TABLE IF NOT EXISTS observations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,             -- 'spot'
    entity_id   UUID NOT NULL,
    metric      TEXT NOT NULL,             -- e.g. 'social_mentions', 'views'
    value       NUMERIC NOT NULL,
    observed_at DATE NOT NULL,
    source_id   UUID REFERENCES sources(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_type, entity_id, metric, observed_at, source_id)
);
CREATE INDEX IF NOT EXISTS idx_observations_entity
    ON observations (entity_type, entity_id, metric, observed_at);

-- Daily trend scores with component breakdown (06: Trend Score内訳)
CREATE TABLE IF NOT EXISTS trend_scores (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spot_id                UUID NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
    score_date             DATE NOT NULL,
    trend_score            NUMERIC(6,2) NOT NULL,
    growth_score           NUMERIC(6,2) NOT NULL DEFAULT 0,
    engagement_score       NUMERIC(6,2) NOT NULL DEFAULT 0,
    recency_score          NUMERIC(6,2) NOT NULL DEFAULT 0,
    seasonality_score      NUMERIC(6,2) NOT NULL DEFAULT 0,
    source_diversity_score NUMERIC(6,2) NOT NULL DEFAULT 0,
    novelty_score          NUMERIC(6,2) NOT NULL DEFAULT 0,
    data_confidence_score  NUMERIC(6,2) NOT NULL DEFAULT 0,
    sample_size            INTEGER NOT NULL DEFAULT 0,
    is_reference           BOOLEAN NOT NULL DEFAULT false,  -- 参考値 (06)
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (spot_id, score_date)
);
CREATE INDEX IF NOT EXISTS idx_trend_scores_date_score
    ON trend_scores (score_date, trend_score DESC);
