import type { RankingItem, Spot } from "../lib/api";
import { yen } from "../lib/api";

export function ScoreBadge({ score, reference }: { score?: number | null; reference?: boolean }) {
  if (score == null) return null;
  return (
    <span className={`badge ${reference ? "ref" : "hot"}`} title={reference ? "参考値 (サンプル/情報源が少ない)" : "Trend Score"}>
      🔥 {score.toFixed(0)}{reference ? " 参考" : ""}
    </span>
  );
}

export function Tags({ tags }: { tags?: string[] }) {
  if (!tags || tags.length === 0) return null;
  return (
    <div className="tagrow">
      {tags.slice(0, 5).map((t) => (
        <span key={t} className="badge">#{t}</span>
      ))}
    </div>
  );
}

export function SpotCard({ spot }: { spot: Spot }) {
  return (
    <a href={`/spots/${spot.id}`} className="card">
      <div className="section-head">
        <span className="title">{spot.name}</span>
        <ScoreBadge score={spot.trend_score} />
      </div>
      <div className="meta">
        {spot.category ?? "—"}
        {spot.distance_m != null ? ` · ${(spot.distance_m / 1000).toFixed(1)}km` : ""}
        {spot.best_season ? ` · ${spot.best_season}` : ""}
      </div>
      {spot.ai_summary && <div className="small muted">{spot.ai_summary}</div>}
      <div className="meta">予算 {yen(spot.estimated_budget_min)}–{yen(spot.estimated_budget_max)}</div>
      <Tags tags={spot.tags} />
      {spot.ai_summary && <span className="badge ai">AI要約</span>}
    </a>
  );
}

export function RankingCard({ item, rank }: { item: RankingItem; rank: number }) {
  return (
    <a href={`/spots/${item.id}`} className="card">
      <div className="section-head">
        <span className="title">{rank}. {item.name}</span>
        <ScoreBadge score={item.trend_score} reference={item.is_reference} />
      </div>
      <div className="meta">{item.category ?? "—"} · {item.score_date}</div>
      {item.ai_summary && <div className="small muted">{item.ai_summary}</div>}
      <div className="small muted">成長 {item.growth_score.toFixed(0)} · 季節 {item.seasonality_score.toFixed(0)} · 新規 {item.novelty_score.toFixed(0)}</div>
      <div className="bar"><span style={{ width: `${Math.min(100, item.trend_score)}%` }} /></div>
    </a>
  );
}
