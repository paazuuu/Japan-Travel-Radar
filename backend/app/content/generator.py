"""Chinese / SNS content generation (09_MVP7_CHINESE_CONTENT.md).

Pipeline: fact extraction -> Chinese translation -> platform adaptation.
Deterministic and template-based so it runs offline and is unit-testable. Only
facts from the DB are used (name, category, tags, season, budget, access, source).
Everything produced is a DRAFT — never auto-published; a human reviews first.
"""

from __future__ import annotations

from dataclasses import dataclass, field

MODEL_ID = "template-zh/v1"

CATEGORY_ZH = {
    "sightseeing": "观光", "nature": "自然风光", "onsen": "温泉", "culture": "文化",
    "event": "活动/祭典", "gourmet": "美食",
}
TAG_ZH = {
    "絶景": "绝景", "写真映え": "出片圣地", "歴史": "历史", "文化": "文化",
    "自然": "自然", "温泉": "温泉", "夜景": "夜景", "海": "海", "山": "山",
    "家族向け": "亲子", "紅葉": "红叶", "桜": "樱花",
}
SEASON_ZH = {"spring": "春季（樱花）", "summer": "夏季", "autumn": "秋季（红叶）", "winter": "冬季", "all": "四季皆宜"}
PHOTO_HINT_ZH = {
    "絶景": "登高远眺的观景台", "夜景": "傍晚到入夜的城市灯光", "桜": "樱花树下",
    "紅葉": "红叶背景", "海": "海边地平线", "写真映え": "标志性地标前",
}


@dataclass
class SpotFacts:
    name: str
    name_zh: str | None = None
    category: str | None = None
    tags: list[str] = field(default_factory=list)
    best_season: list[str] = field(default_factory=list)
    budget_min: int | None = None
    budget_max: int | None = None
    access: str | None = None
    stay_min: int | None = None
    summary: str | None = None
    source_url: str | None = None


def _zh_name(f: SpotFacts) -> str:
    return f.name_zh or f.name


def _tags_zh(f: SpotFacts) -> list[str]:
    return [TAG_ZH.get(t, t) for t in f.tags]


def _seasons_zh(f: SpotFacts) -> str:
    if not f.best_season:
        return "四季皆宜"
    return "、".join(SEASON_ZH.get(s, s) for s in f.best_season)


def _budget_zh(f: SpotFacts) -> str:
    if f.budget_min is None and f.budget_max is None:
        return "免费或低消费"
    lo = f.budget_min or 0
    hi = f.budget_max or lo
    return f"约 ¥{lo}–{hi}（日元）"


def _photo_zh(f: SpotFacts) -> str:
    for t in f.tags:
        if t in PHOTO_HINT_ZH:
            return PHOTO_HINT_ZH[t]
    return "标志性景观处"


def _needs_review_note() -> str:
    return "（AI草稿，发布前请人工校对翻译与事实）"


def xiaohongshu(f: SpotFacts) -> dict:
    name = _zh_name(f)
    tags = _tags_zh(f)
    return {
        "标题": f"【关西宝藏】{name}｜{('・'.join(tags[:2])) or '值得一去'}",
        "地点": f"{name}（日本·关西）",
        "为什么值得去": f.summary or f"{name} 是关西地区的{CATEGORY_ZH.get(f.category or '', '热门')}地点。",
        "交通": f.access or "建议查询官方交通信息",
        "预算": _budget_zh(f),
        "推荐时间": _seasons_zh(f),
        "拍照位置": _photo_zh(f),
        "美食": "可搭配周边餐厅（详见 App 附近美食）",
        "注意事项": _needs_review_note(),
        "标签": [f"#{t}" for t in tags] + ["#关西旅行", "#日本旅行"],
        "_source_url": f.source_url,
    }


def wechat(f: SpotFacts) -> dict:
    name = _zh_name(f)
    paras = [
        f"{name} 位于日本关西地区，是一处{CATEGORY_ZH.get(f.category or '', '值得一游')}的目的地。",
        (f.summary or "").strip() or f"{name} 以其独特的景观吸引着众多旅行者。",
        f"最佳前往时间：{_seasons_zh(f)}。建议停留 {f.stay_min or 90} 分钟左右。",
        f"预算参考：{_budget_zh(f)}。",
        f"交通：{f.access or '请参考官方信息'}。",
        f"信息来源：{f.source_url or '本站数据库'}。{_needs_review_note()}",
    ]
    return {
        "标题": f"{name}：关西深度旅行指南",
        "正文": paras,
        "_source_url": f.source_url,
    }


def video_script(f: SpotFacts) -> dict:
    name = _zh_name(f)
    tags = _tags_zh(f)
    scenes = [
        {"time": "0-3秒", "type": "Hook", "text": f"你还没去过关西的{name}？"},
        {"time": "3-10秒", "type": "场所介绍", "text": f"{name}，日本关西的{CATEGORY_ZH.get(f.category or '', '人气')}地点。"},
        {"time": "10-30秒", "type": "见どころ", "text": (f.summary or f"{name}的看点：{('、'.join(tags[:3])) or '绝美风景'}。")},
        {"time": "30-45秒", "type": "美食", "text": "别忘了品尝周边的当地美食。"},
        {"time": "45-60秒", "type": "交通・预算", "text": f"交通：{f.access or '见官方信息'}；预算 {_budget_zh(f)}。"},
    ]
    return {"标题": f"60秒玩转 {name}", "scenes": scenes, "note": _needs_review_note(), "_source_url": f.source_url}


PLATFORMS = {
    "xiaohongshu": xiaohongshu,
    "wechat": wechat,
    "video_script": video_script,
}


def generate(platform: str, facts: SpotFacts) -> dict:
    fn = PLATFORMS.get(platform)
    if fn is None:
        raise ValueError(f"unknown platform: {platform}")
    return fn(facts)
