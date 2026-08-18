"""Spot analysis (05_MVP3_AI_ANALYSIS.md).

Produces the fixed structured output:
  { summary, categories, tags, best_season, travel_types, food_tags, confidence }

Primary implementation is a deterministic rule-based classifier so the pipeline
runs offline and is unit-testable. When AI_API_KEY is configured the LLM path
(ai_client) can refine results, but it must return the same schema and never
invent facts (hours, prices, "open now") — see 05 "行わせない".
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

MODEL_ID = "rule-based/v1"

# Keyword -> spot tag (05 スポットタグ)
_TAG_RULES: dict[str, list[str]] = {
    "絶景": ["絶景", "展望", "夜景", "パノラマ", "大観覧車", "タワー", "大橋", "滝"],
    "写真映え": ["映え", "紅葉", "桜", "イルミ", "ライトアップ", "花灯路", "ルミナリエ"],
    "歴史": ["城", "城跡", "神社", "大社", "寺", "寺院", "遺跡", "史跡", "博物館"],
    "文化": ["美術館", "博物館", "文化", "図書館", "建築"],
    "自然": ["公園", "山", "湖", "滝", "海", "ビーチ", "島", "植物園", "高原"],
    "温泉": ["温泉", "湯"],
    "夜景": ["夜景", "ルミナリエ", "イルミ"],
    "海": ["海", "ビーチ", "海峡", "港", "水族館", "島"],
    "山": ["山", "高原", "六甲", "高野"],
    "家族向け": ["水族館", "動物", "テーマパーク", "科学館", "公園", "パンダ"],
    "紅葉": ["紅葉", "もみじ"],
    "桜": ["桜", "花見"],
}

# Keyword -> category (normalized)
_CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("nature", ["公園", "山", "湖", "滝", "海", "ビーチ", "島", "高原", "植物園", "自然"]),
    ("onsen", ["温泉", "湯"]),
    ("culture", ["美術館", "博物館", "図書館", "文化", "建築"]),
    ("event", ["祭", "まつり", "イルミ", "ルミナリエ", "花灯路"]),
    ("gourmet", ["市場", "グルメ", "食"]),
    ("sightseeing", ["城", "神社", "大社", "寺", "タワー", "展望", "橋", "観覧車"]),
]

# Keyword -> season
_SEASON_RULES: dict[str, list[str]] = {
    "spring": ["桜", "花見", "春"],
    "summer": ["海", "ビーチ", "祭", "花火", "夏"],
    "autumn": ["紅葉", "もみじ", "秋"],
    "winter": ["温泉", "イルミ", "ルミナリエ", "雪", "冬"],
}

# Keyword -> travel type
_TRAVEL_RULES: dict[str, list[str]] = {
    "family": ["水族館", "動物", "テーマパーク", "科学館", "公園", "パンダ"],
    "couple": ["夜景", "イルミ", "展望", "ルミナリエ"],
    "solo": ["寺", "神社", "美術館", "博物館"],
    "day_trip": ["公園", "城", "神社", "温泉", "市場"],
}

# Food keyword -> food tag (05 食タグ)
_FOOD_RULES: dict[str, list[str]] = {
    "魚": ["魚", "海鮮", "まぐろ", "寿司", "鮨"],
    "寿司": ["寿司", "鮨", "すし"],
    "海鮮": ["海鮮", "まぐろ", "かに", "蟹"],
    "肉": ["牛", "肉", "ステーキ", "焼肉", "串カツ"],
    "麺": ["ラーメン", "そば", "うどん", "そうめん", "ちゃんぽん", "麺"],
    "郷土料理": ["郷土", "名物", "specialty"],
    "野菜": ["野菜", "湯葉", "おばんざい"],
    "スイーツ": ["スイーツ", "甘味", "パフェ"],
    "カフェ": ["カフェ", "coffee"],
}


@dataclass
class AnalysisResult:
    summary: str
    categories: list[str]
    tags: list[str]
    best_season: list[str]
    travel_types: list[str]
    food_tags: list[str]
    confidence: float
    evidence: str
    model: str = MODEL_ID

    def to_dict(self) -> dict:
        return asdict(self)


def _match(text: str, rules) -> list[str]:
    hits: list[str] = []
    for label, kws in (rules.items() if isinstance(rules, dict) else rules):
        if any(kw.lower() in text for kw in kws):
            hits.append(label)
    return hits


def analyze(name: str, description: str | None = None,
            category: str | None = None) -> AnalysisResult:
    """Rule-based classification. Deterministic and side-effect free."""
    text = f"{name} {description or ''} {category or ''}".lower()

    tags = _match(text, _TAG_RULES)
    categories = [c for c, kws in _CATEGORY_RULES if any(kw.lower() in text for kw in kws)]
    if category and category not in categories:
        categories.insert(0, category)
    best_season = _match(text, _SEASON_RULES)
    travel_types = _match(text, _TRAVEL_RULES)
    food_tags = _match(text, _FOOD_RULES)

    # Confidence reflects how much signal we found (05: 根拠がなければ低信頼).
    signals = len(tags) + len(categories) + len(best_season) + len(travel_types)
    if signals == 0:
        confidence = 0.2
        evidence = "no keyword signal; classification is a weak guess"
    else:
        confidence = round(min(0.55 + 0.08 * signals, 0.95), 2)
        evidence = f"matched {signals} keyword signals in name/description"

    summary = (description or name).strip()
    if len(summary) > 140:
        summary = summary[:137] + "…"

    return AnalysisResult(
        summary=summary,
        categories=categories or ([category] if category else []),
        tags=sorted(set(tags)),
        best_season=sorted(set(best_season)),
        travel_types=sorted(set(travel_types)),
        food_tags=sorted(set(food_tags)),
        confidence=confidence,
        evidence=evidence,
    )
