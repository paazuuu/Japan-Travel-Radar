-- MVP7: Chinese / SNS content drafts (09_MVP7_CHINESE_CONTENT.md).
-- Draft-only by design: nothing is auto-published; every row starts unreviewed.

CREATE TABLE IF NOT EXISTS content_drafts (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spot_id      UUID NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
    platform     TEXT NOT NULL,            -- xiaohongshu / wechat / video_script
    language     TEXT NOT NULL DEFAULT 'zh-CN',
    title        TEXT,
    body         JSONB NOT NULL DEFAULT '{}',  -- structured sections per platform
    status       TEXT NOT NULL DEFAULT 'draft', -- draft / approved / rejected
    reviewed     BOOLEAN NOT NULL DEFAULT false,
    model        TEXT NOT NULL,
    source_url   TEXT,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (spot_id, platform)
);

CREATE INDEX IF NOT EXISTS idx_content_drafts_spot ON content_drafts (spot_id);
CREATE INDEX IF NOT EXISTS idx_content_drafts_status ON content_drafts (status);
