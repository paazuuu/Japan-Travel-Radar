-- Feature A: image URLs (12: 画像はURL/ライセンス/帰属を保存、原則DBに実体を持たない).

ALTER TABLE spots       ADD COLUMN IF NOT EXISTS image_url     TEXT;
ALTER TABLE spots       ADD COLUMN IF NOT EXISTS image_license TEXT;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS image_url     TEXT;
ALTER TABLE restaurants ADD COLUMN IF NOT EXISTS image_license TEXT;
ALTER TABLE events      ADD COLUMN IF NOT EXISTS image_url     TEXT;
ALTER TABLE events      ADD COLUMN IF NOT EXISTS image_license TEXT;
