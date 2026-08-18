"""Ranking job (MVP4): build features per spot, compute Trend Score, persist.

Growth uses `observations` (current vs previous period). Other components come
from data we already hold (recency, seasonality, source diversity, novelty,
AI confidence), so rankings vary meaningfully even before social data exists.
"""

from __future__ import annotations

from datetime import date

import db as dbmod
from scorer import compute


def _features_sql() -> str:
    # One row per spot with everything the scorer needs.
    return """
    WITH latest_obs AS (
        SELECT DISTINCT ON (entity_id) entity_id, value AS current_val, observed_at
        FROM observations
        WHERE entity_type = 'spot' AND metric = 'social_mentions'
        ORDER BY entity_id, observed_at DESC
    ),
    prev_obs AS (
        SELECT o.entity_id, o.value AS previous_val
        FROM observations o
        JOIN latest_obs l ON l.entity_id = o.entity_id AND o.observed_at < l.observed_at
        WHERE o.entity_type = 'spot' AND o.metric = 'social_mentions'
        ORDER BY o.entity_id, o.observed_at DESC
    ),
    obs_count AS (
        SELECT entity_id, count(*) AS n
        FROM observations WHERE entity_type = 'spot' AND metric = 'social_mentions'
        GROUP BY entity_id
    ),
    src_div AS (
        SELECT s.id AS spot_id,
               (SELECT count(DISTINCT r.source_key) FROM raw_items r
                 WHERE r.external_id = s.external_id) + 1 AS source_count
        FROM spots s
    )
    SELECT
        s.id,
        s.best_season,
        a.best_season AS ai_best_season,
        a.confidence,
        EXTRACT(EPOCH FROM (now() - s.updated_at)) / 86400.0 AS updated_days_ago,
        EXTRACT(EPOCH FROM (now() - s.created_at)) / 86400.0 AS created_days_ago,
        lo.current_val,
        po.previous_val,
        COALESCE(oc.n, 0) AS sample_size,
        COALESCE(sd.source_count, 1) AS source_count
    FROM spots s
    LEFT JOIN spot_analyses a ON a.spot_id = s.id
    LEFT JOIN latest_obs lo ON lo.entity_id = s.id
    LEFT JOIN prev_obs po ON po.entity_id = s.id
    LEFT JOIN obs_count oc ON oc.entity_id = s.id
    LEFT JOIN src_div sd ON sd.spot_id = s.id
    WHERE s.status = 'published'
    """


def run_ranking_once() -> int:
    conn = dbmod.connect()
    today = date.today()
    month = today.month
    updated = 0
    try:
        with conn.cursor() as cur:
            cur.execute(_features_sql())
            rows = cur.fetchall()
            cols = [d.name for d in cur.description]

        for row in rows:
            r = dict(zip(cols, row))
            seasons: list[str] = []
            if r.get("ai_best_season"):
                seasons = list(r["ai_best_season"])
            elif r.get("best_season"):
                seasons = [r["best_season"]]

            breakdown = compute({
                "current_metric": float(r["current_val"]) if r["current_val"] is not None else None,
                "previous_metric": float(r["previous_val"]) if r["previous_val"] is not None else None,
                "engagement_count": float(r["current_val"]) if r["current_val"] is not None else 0,
                "updated_days_ago": float(r["updated_days_ago"] or 999),
                "created_days_ago": float(r["created_days_ago"] or 999),
                "best_seasons": seasons,
                "month": month,
                "source_count": int(r["source_count"] or 1),
                "confidence": float(r["confidence"]) if r["confidence"] is not None else 0.0,
                "sample_size": int(r["sample_size"] or 0),
            })
            _upsert_trend(conn, r["id"], today, breakdown)
            updated += 1
        conn.commit()
        print(f"[worker] ranking done. scored={updated}", flush=True)
        return updated
    finally:
        conn.close()


def _upsert_trend(conn, spot_id, score_date, b) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO trend_scores
              (spot_id, score_date, trend_score, growth_score, engagement_score,
               recency_score, seasonality_score, source_diversity_score, novelty_score,
               data_confidence_score, sample_size, is_reference)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (spot_id, score_date) DO UPDATE SET
              trend_score = EXCLUDED.trend_score,
              growth_score = EXCLUDED.growth_score,
              engagement_score = EXCLUDED.engagement_score,
              recency_score = EXCLUDED.recency_score,
              seasonality_score = EXCLUDED.seasonality_score,
              source_diversity_score = EXCLUDED.source_diversity_score,
              novelty_score = EXCLUDED.novelty_score,
              data_confidence_score = EXCLUDED.data_confidence_score,
              sample_size = EXCLUDED.sample_size,
              is_reference = EXCLUDED.is_reference
            """,
            (spot_id, score_date, b.trend_score, b.growth_score, b.engagement_score,
             b.recency_score, b.seasonality_score, b.source_diversity_score,
             b.novelty_score, b.data_confidence_score, b.sample_size, b.is_reference),
        )
