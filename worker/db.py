"""Database access for the analysis worker (psycopg 3)."""

from __future__ import annotations

import json
import os

import psycopg

from analyzer import AnalysisResult


def _dsn() -> str:
    url = os.environ.get("DATABASE_URL", "postgresql://travel:CHANGE_ME@postgres:5432/japan_travel")
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def connect() -> psycopg.Connection:
    return psycopg.connect(_dsn())


def fetch_spots_needing_analysis(conn: psycopg.Connection, limit: int = 500) -> list[tuple]:
    """Spots with no analysis yet, or edited after their last analysis."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.name, s.description, s.category
            FROM spots s
            LEFT JOIN spot_analyses a ON a.spot_id = s.id
            WHERE a.id IS NULL OR (a.reviewed = false AND s.updated_at > a.generated_at)
            ORDER BY s.updated_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall()


def upsert_analysis(conn: psycopg.Connection, spot_id: str, result: AnalysisResult) -> None:
    with conn.cursor() as cur:
        # Do not clobber a human-reviewed analysis.
        cur.execute("SELECT reviewed FROM spot_analyses WHERE spot_id = %s", (spot_id,))
        row = cur.fetchone()
        if row and row[0]:
            return

        cur.execute(
            """
            INSERT INTO spot_analyses (spot_id, summary, categories, tags, best_season,
                                       travel_types, food_tags, confidence, evidence, model)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (spot_id) DO UPDATE SET
                summary = EXCLUDED.summary,
                categories = EXCLUDED.categories,
                tags = EXCLUDED.tags,
                best_season = EXCLUDED.best_season,
                travel_types = EXCLUDED.travel_types,
                food_tags = EXCLUDED.food_tags,
                confidence = EXCLUDED.confidence,
                evidence = EXCLUDED.evidence,
                model = EXCLUDED.model,
                generated_at = now()
            """,
            (
                spot_id,
                result.summary,
                json.dumps(result.categories, ensure_ascii=False),
                json.dumps(result.tags, ensure_ascii=False),
                json.dumps(result.best_season, ensure_ascii=False),
                json.dumps(result.travel_types, ensure_ascii=False),
                json.dumps(result.food_tags, ensure_ascii=False),
                result.confidence,
                result.evidence,
                result.model,
            ),
        )

        # Refresh AI-origin tags only; leave manual tags untouched.
        cur.execute("DELETE FROM spot_tags WHERE spot_id = %s AND origin = 'ai'", (spot_id,))
        for tag in result.tags:
            cur.execute(
                """
                INSERT INTO spot_tags (spot_id, tag, origin, confidence)
                VALUES (%s, %s, 'ai', %s)
                ON CONFLICT (spot_id, tag) DO UPDATE SET origin = 'ai', confidence = EXCLUDED.confidence
                """,
                (spot_id, tag, result.confidence),
            )
    conn.commit()
