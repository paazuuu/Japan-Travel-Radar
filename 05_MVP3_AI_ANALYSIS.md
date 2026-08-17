# 05 — MVP3 AI分析仕様

## 目的

収集した情報を旅行者が使える構造化データへ変換する。

## AI処理

```text
Raw/Normalized Data
       ↓
Language Detection
       ↓
Summarization
       ↓
Category
       ↓
Tags
       ↓
Season
       ↓
Travel Type
       ↓
Food Attributes
       ↓
Quality Check
```

## スポットタグ

例:

```text
絶景
写真映え
穴場
家族向け
デート
一人旅
雨の日
桜
紅葉
雪
温泉
海
山
歴史
文化
夜景
```

## 食タグ

```text
魚
肉
寿司
海鮮
麺
郷土料理
野菜
ベジタリアン
ヴィーガン
スイーツ
カフェ
```

AIが推測した情報には `confidence` を付け、根拠がない場合は「不明」とする。

## AIの役割

### 行ってよい
- 要約
- 分類
- タグ付け
- 類似スポット判定
- 旅行者条件との適合度計算
- 中国語翻訳
- SNS投稿案生成

### 行わせない
- 出典なしの営業時間創作
- 存在しない店舗創作
- 交通費の根拠なき確定
- 「営業中」などリアルタイム情報の断定

## Structured Output

AIの返却値はJSON Schemaで固定する。

```json
{
  "summary": "...",
  "categories": ["nature"],
  "tags": ["scenic", "photogenic"],
  "best_season": ["autumn"],
  "travel_types": ["couple", "day_trip"],
  "food_tags": [],
  "confidence": 0.91
}
```

## 完了条件

- 100スポットをAI分類
- タグの一貫性を確認
- AI生成データと原情報を分離
- 人間による修正が可能
