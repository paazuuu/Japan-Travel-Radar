-- MVP1: core travel database schema (03_MVP1_DATABASE.md, 17_DATA_MODEL_DETAIL.md).
-- Geography(Point,4326) for spatial columns; UUID PKs via pgcrypto (gen_random_uuid).

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------------
-- Geography hierarchy (nationwide-ready: region -> prefecture -> city)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        TEXT UNIQUE NOT NULL,          -- e.g. 'kansai'
    name        TEXT NOT NULL,
    name_en     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS prefectures (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id   UUID NOT NULL REFERENCES regions(id) ON DELETE RESTRICT,
    code        TEXT UNIQUE NOT NULL,          -- JIS-like code, e.g. '27' for Osaka
    name        TEXT NOT NULL,
    name_en     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cities (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prefecture_id UUID NOT NULL REFERENCES prefectures(id) ON DELETE RESTRICT,
    name          TEXT NOT NULL,
    name_en       TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (prefecture_id, name)
);

-- ---------------------------------------------------------------------------
-- Sources (provenance of every collected record)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sources (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type       TEXT NOT NULL,           -- official / opendata / rss / web / api ...
    source_name       TEXT NOT NULL,
    source_url        TEXT,
    license_note      TEXT,
    collection_method TEXT,
    last_collected_at TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Spots
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS spots (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                     TEXT NOT NULL,
    name_en                  TEXT,
    name_zh                  TEXT,
    description              TEXT,
    prefecture_id            UUID REFERENCES prefectures(id) ON DELETE SET NULL,
    city_id                  UUID REFERENCES cities(id) ON DELETE SET NULL,
    location                 GEOGRAPHY(POINT, 4326),
    category                 TEXT,
    subcategory              TEXT,
    best_season              TEXT,
    recommended_stay_minutes INTEGER,
    estimated_budget_min     INTEGER,
    estimated_budget_max     INTEGER,
    access_text              TEXT,
    official_url             TEXT,
    source_id                UUID REFERENCES sources(id) ON DELETE SET NULL,
    source_url               TEXT,
    status                   TEXT NOT NULL DEFAULT 'published',  -- published / draft / hidden
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Restaurants (independent of spots; attributes change often)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS restaurants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    prefecture_id   UUID REFERENCES prefectures(id) ON DELETE SET NULL,
    city_id         UUID REFERENCES cities(id) ON DELETE SET NULL,
    location        GEOGRAPHY(POINT, 4326),
    category        TEXT,
    price_min       INTEGER,
    price_max       INTEGER,
    fish            BOOLEAN NOT NULL DEFAULT false,
    meat            BOOLEAN NOT NULL DEFAULT false,
    vegetarian      BOOLEAN NOT NULL DEFAULT false,
    vegan           BOOLEAN NOT NULL DEFAULT false,
    local_specialty BOOLEAN NOT NULL DEFAULT false,
    reservation_url TEXT,
    official_url    TEXT,
    source_id       UUID REFERENCES sources(id) ON DELETE SET NULL,
    source_url      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Events
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT NOT NULL,
    prefecture_id UUID REFERENCES prefectures(id) ON DELETE SET NULL,
    location      GEOGRAPHY(POINT, 4326),
    start_at      TIMESTAMPTZ,
    end_at        TIMESTAMPTZ,
    category      TEXT,
    official_url  TEXT,
    source_id     UUID REFERENCES sources(id) ON DELETE SET NULL,
    source_url    TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Tags
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS spot_tags (
    id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spot_id  UUID NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
    tag      TEXT NOT NULL,
    UNIQUE (spot_id, tag)
);

CREATE TABLE IF NOT EXISTS food_tags (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    tag           TEXT NOT NULL,
    confidence    NUMERIC(4,3),
    source_url    TEXT,
    UNIQUE (restaurant_id, tag)
);

-- ---------------------------------------------------------------------------
-- Indexes (03 必須インデックス)
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_spots_location      ON spots USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_spots_prefecture    ON spots (prefecture_id);
CREATE INDEX IF NOT EXISTS idx_spots_city          ON spots (city_id);
CREATE INDEX IF NOT EXISTS idx_spots_category      ON spots (category);
CREATE INDEX IF NOT EXISTS idx_spots_updated_at    ON spots (updated_at);
CREATE INDEX IF NOT EXISTS idx_spots_name_trgm     ON spots USING GIN (name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_restaurants_location   ON restaurants USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_restaurants_prefecture ON restaurants (prefecture_id);
CREATE INDEX IF NOT EXISTS idx_restaurants_category   ON restaurants (category);

CREATE INDEX IF NOT EXISTS idx_events_location ON events USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_events_start_at ON events (start_at);
