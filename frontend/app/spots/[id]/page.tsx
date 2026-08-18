import { api, yen } from "../../../lib/api";
import { Tags } from "../../../components/SpotCard";

export const dynamic = "force-dynamic";

export default async function SpotDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const spot = await api.spot(id);

  if (!spot) {
    return (
      <main>
        <p className="muted">スポットが見つかりませんでした。</p>
        <a className="link" href="/">← Home</a>
      </main>
    );
  }

  const [nearbySpots, nearbyFood] = await Promise.all([
    spot.lat != null && spot.lng != null ? api.nearbySpots(spot.lat, spot.lng, 5000) : Promise.resolve([]),
    spot.lat != null && spot.lng != null ? api.nearbyRestaurants(spot.lat, spot.lng, "&radius=5000") : Promise.resolve([]),
  ]);

  return (
    <main>
      <a className="small muted" href="/">← Home</a>
      <div className="section-head">
        <h1>{spot.name}</h1>
        {spot.trend_score != null && <span className="badge hot">🔥 {spot.trend_score.toFixed(0)}</span>}
      </div>
      <div className="meta">
        {spot.category ?? "—"}{spot.subcategory ? ` / ${spot.subcategory}` : ""}
        {spot.best_season ? ` · おすすめ: ${spot.best_season}` : ""}
      </div>

      {spot.ai_summary && (
        <p>
          {spot.ai_summary} <span className="badge ai">AI要約{spot.ai_confidence != null ? ` (信頼度 ${(spot.ai_confidence * 100).toFixed(0)}%)` : ""}</span>
        </p>
      )}
      {spot.description && spot.description !== spot.ai_summary && <p className="muted">{spot.description}</p>}

      <Tags tags={spot.tags} />

      <div className="card" style={{ marginTop: "1rem" }}>
        <div className="meta">滞在目安: {spot.recommended_stay_minutes ?? "—"} 分</div>
        <div className="meta">予算: {yen(spot.estimated_budget_min)}–{yen(spot.estimated_budget_max)}</div>
        <div className="meta">アクセス: {spot.access_text ?? "—"}</div>
        <div className="tagrow">
          {spot.official_url && <a className="badge official" href={spot.official_url} target="_blank" rel="noreferrer">公式サイト</a>}
          {spot.source_url && <a className="badge" href={spot.source_url} target="_blank" rel="noreferrer">出典</a>}
          <a className="badge ai" href={`/content?spot=${spot.id}`}>中国語コンテンツ生成</a>
        </div>
      </div>

      <h2>近くのグルメ</h2>
      <div className="grid">
        {(nearbyFood ?? []).slice(0, 6).map((r) => (
          <div key={r.id} className="card">
            <div className="title">{r.name}</div>
            <div className="meta">{r.category ?? "—"} · {(r.distance_m! / 1000).toFixed(1)}km</div>
          </div>
        ))}
      </div>

      <h2>近くのスポット</h2>
      <div className="grid">
        {(nearbySpots ?? []).filter((s) => s.id !== spot.id).slice(0, 6).map((s) => (
          <a key={s.id} href={`/spots/${s.id}`} className="card">
            <div className="title">{s.name}</div>
            <div className="meta">{s.category ?? "—"} · {(s.distance_m! / 1000).toFixed(1)}km</div>
          </a>
        ))}
      </div>
    </main>
  );
}
