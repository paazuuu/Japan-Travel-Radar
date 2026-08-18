"""MVP7: Chinese content generator unit tests (no DB / no network)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("DATABASE_URL", "postgresql://x:x@127.0.0.1:1/none")

from app.content import generator as gen  # noqa: E402

FACTS = gen.SpotFacts(
    name="大阪城", name_zh="大阪城", category="sightseeing",
    tags=["歴史", "絶景"], best_season=["spring"], budget_min=600, budget_max=1500,
    access="JR大阪城公園駅 徒歩", stay_min=120, summary="大阪的象征。",
    source_url="http://example/osaka",
)


def test_xiaohongshu_sections_present():
    r = gen.xiaohongshu(FACTS)
    for key in ["标题", "地点", "为什么值得去", "交通", "预算", "推荐时间", "拍照位置", "美食", "注意事项"]:
        assert key in r
    assert "绝景" in " ".join(r["标签"]) or any("绝景" in t for t in r["标签"])
    assert r["_source_url"] == "http://example/osaka"


def test_wechat_has_title_and_paragraphs():
    r = gen.wechat(FACTS)
    assert r["标题"]
    assert isinstance(r["正文"], list) and len(r["正文"]) >= 4


def test_video_script_covers_60_seconds():
    r = gen.video_script(FACTS)
    times = [s["time"] for s in r["scenes"]]
    assert times == ["0-3秒", "3-10秒", "10-30秒", "30-45秒", "45-60秒"]


def test_budget_and_season_translation():
    assert "¥600" in gen._budget_zh(FACTS)
    assert "春" in gen._seasons_zh(FACTS)


def test_generate_dispatch_and_unknown():
    assert gen.generate("wechat", FACTS)["标题"]
    try:
        gen.generate("weibo", FACTS)
        assert False
    except ValueError:
        pass
