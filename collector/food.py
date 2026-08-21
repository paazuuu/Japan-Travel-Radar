"""Food attribute inference for restaurants (pure; unit-tested).

Maps an OSM/cuisine string + name into the boolean food attributes and food
tags the app uses. Fact-based only (keyword match) — no fabrication.
"""

from __future__ import annotations

# keyword -> attribute
_FISH = ["sushi", "seafood", "fish", "寿司", "鮨", "海鮮", "魚", "まぐろ", "kaisen"]
_MEAT = ["yakiniku", "steak", "barbecue", "bbq", "burger", "meat", "焼肉", "ステーキ",
         "串カツ", "とんかつ", "唐揚"]
_VEG = ["vegetarian", "野菜", "湯葉", "おばんざい", "精進"]
_VEGAN = ["vegan", "ヴィーガン", "ビーガン"]
_LOCAL = ["japanese", "regional", "ramen", "udon", "soba", "okonomiyaki", "takoyaki",
          "郷土", "名物", "ラーメン", "うどん", "そば", "お好み焼", "たこ焼", "郷土料理"]

# cuisine token -> normalized category
_CATEGORY = {
    "sushi": "sushi", "seafood": "seafood", "ramen": "ramen", "noodle": "noodles",
    "udon": "noodles", "soba": "noodles", "yakiniku": "yakiniku", "steak": "steak",
    "cafe": "cafe", "italian": "italian", "japanese": "japanese",
}


def _hit(text: str, kws: list[str]) -> bool:
    return any(k in text for k in kws)


def infer_food(cuisine: str | None, name: str | None = None) -> dict:
    """Return {category, fish, meat, vegetarian, vegan, local_specialty, tags}."""
    text = f"{cuisine or ''} {name or ''}".lower()

    fish = _hit(text, _FISH)
    meat = _hit(text, _MEAT)
    veg = _hit(text, _VEG)
    vegan = _hit(text, _VEGAN)
    local = _hit(text, _LOCAL)

    category = None
    for token, cat in _CATEGORY.items():
        if token in text:
            category = cat
            break

    tags: list[str] = []
    if fish:
        tags.append("魚")
    if "sushi" in text or "寿司" in text or "鮨" in text:
        tags.append("寿司")
    if "seafood" in text or "海鮮" in text:
        tags.append("海鮮")
    if meat:
        tags.append("肉")
    if _hit(text, ["ramen", "udon", "soba", "noodle", "ラーメン", "うどん", "そば", "麺"]):
        tags.append("麺")
    if veg:
        tags.append("野菜")
    if vegan:
        tags.append("ヴィーガン")
    if local:
        tags.append("郷土料理")
    if "cafe" in text or "カフェ" in text:
        tags.append("カフェ")

    return {
        "category": category or "restaurant",
        "fish": fish, "meat": meat, "vegetarian": veg, "vegan": vegan,
        "local_specialty": local, "tags": sorted(set(tags)),
    }
