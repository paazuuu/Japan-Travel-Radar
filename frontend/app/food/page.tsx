import { api, yen } from "../../lib/api";
import { Thumb } from "../../components/SpotCard";

export const dynamic = "force-dynamic";

function attrs(r: {
  fish: boolean; meat: boolean; vegetarian: boolean; vegan: boolean; local_specialty: boolean;
}) {
  const out: string[] = [];
  if (r.fish) out.push("魚");
  if (r.meat) out.push("肉");
  if (r.vegetarian) out.push("野菜");
  if (r.vegan) out.push("ヴィーガン");
  if (r.local_specialty) out.push("郷土料理");
  return out;
}

export default async function FoodPage({
  searchParams,
}: {
  searchParams: Promise<{ fish?: string }>;
}) {
  const sp = await searchParams;
  const filter = sp.fish === "true" ? "fish=true&" : "";
  const restaurants = await api.restaurants(`${filter}limit=50`);

  return (
    <main>
      <h1>グルメ</h1>
      <div className="tabs">
        <a href="/food" className={!sp.fish ? "active" : ""}>すべて</a>
        <a href="/food?fish=true" className={sp.fish === "true" ? "active" : ""}>魚・海鮮</a>
      </div>
      <div className="grid">
        {(restaurants ?? []).map((r) => (
          <div key={r.id} className="card">
            <Thumb src={r.image_url} alt={r.name} emoji="🍽" />
            <div className="title">{r.name}</div>
            <div className="meta">{r.category ?? "—"} · {yen(r.price_min)}–{yen(r.price_max)}</div>
            <div className="tagrow">{attrs(r).map((a) => <span key={a} className="badge">{a}</span>)}</div>
            {r.source_url && (
              <a className="badge official small" href={r.source_url} target="_blank" rel="noreferrer">出典</a>
            )}
          </div>
        ))}
      </div>
      {(!restaurants || restaurants.length === 0) && (
        <p className="muted">データがありません。scripts/seed.sh を実行してください。</p>
      )}
    </main>
  );
}
