"use client";

import { useState } from "react";
import { browserBase, yen } from "../../lib/api";

interface PlanItem {
  sequence: number;
  kind: string;
  label: string;
  start_time?: string | null;
  end_time?: string | null;
  estimated_cost: number;
  travel_time: number;
  spot_id?: string | null;
  source_url?: string | null;
}
interface Plan {
  id: string;
  origin: string;
  transport: string;
  summary?: string | null;
  total_cost?: number | null;
  within_budget?: boolean | null;
  items: PlanItem[];
}

const ICON: Record<string, string> = { depart: "🚉", spot: "📸", meal: "🍽", cafe: "☕", return: "🏠" };

export default function PlannerPage() {
  const [form, setForm] = useState({
    origin: "大阪", budget: 5000, party_size: 2, transport: "train", purpose: "絶景", food: "魚", max_spots: 3,
  });
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    setLoading(true); setError(null); setPlan(null);
    try {
      const res = await fetch(`${browserBase()}/api/v1/planner/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, days: 1 }),
      });
      if (!res.ok) {
        setError(`生成に失敗しました (${res.status})。seedデータが必要です。`);
        return;
      }
      setPlan(await res.json());
    } catch (e: any) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  const set = (k: string, v: string | number) => setForm({ ...form, [k]: v });
  const sources = plan?.items.filter((i) => i.source_url) ?? [];

  return (
    <main>
      <h1>AI旅行プランナー</h1>
      <p className="small muted">DBに登録された実データだけでプランを作ります（存在しない場所は追加しません）。</p>

      <div className="card" style={{ gap: "0.6rem" }}>
        <label className="small">出発地
          <input value={form.origin} onChange={(e) => set("origin", e.target.value)} style={inp} />
        </label>
        <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap" }}>
          <label className="small">予算(円)
            <input type="number" value={form.budget} onChange={(e) => set("budget", Number(e.target.value))} style={inp} />
          </label>
          <label className="small">人数
            <input type="number" value={form.party_size} onChange={(e) => set("party_size", Number(e.target.value))} style={inp} />
          </label>
          <label className="small">スポット数
            <input type="number" value={form.max_spots} onChange={(e) => set("max_spots", Number(e.target.value))} style={inp} />
          </label>
        </div>
        <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap" }}>
          <label className="small">移動
            <select value={form.transport} onChange={(e) => set("transport", e.target.value)} style={inp}>
              <option value="train">電車</option><option value="car">車</option><option value="walk">徒歩</option>
            </select>
          </label>
          <label className="small">目的
            <input value={form.purpose} onChange={(e) => set("purpose", e.target.value)} style={inp} />
          </label>
          <label className="small">食事
            <input value={form.food} onChange={(e) => set("food", e.target.value)} style={inp} />
          </label>
        </div>
        <button onClick={generate} disabled={loading} style={btn}>
          {loading ? "生成中…" : "プランを生成"}
        </button>
      </div>

      {error && <p className="muted small">{error}</p>}

      {plan && (
        <section style={{ marginTop: "1.25rem" }}>
          <h2>プラン</h2>
          <p>{plan.summary}</p>
          <span className={`badge ${plan.within_budget ? "official" : "hot"}`}>
            合計 {yen(plan.total_cost)}（{plan.within_budget ? "予算内" : "予算超過"}）
          </span>

          <div style={{ marginTop: "1rem" }}>
            {plan.items.map((it) => (
              <div key={it.sequence} className="card" style={{ marginBottom: "0.5rem", flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <div className="title">{ICON[it.kind] ?? "•"} {it.start_time} {it.label}</div>
                  <div className="small muted">
                    {it.travel_time > 0 ? `移動 ${it.travel_time}分` : ""}{it.estimated_cost > 0 ? ` · ${yen(it.estimated_cost)}` : ""}
                    {it.spot_id ? " · " : ""}
                    {it.spot_id && <a href={`/spots/${it.spot_id}`}>詳細</a>}
                  </div>
                </div>
                {it.source_url && <a className="badge" href={it.source_url} target="_blank" rel="noreferrer">出典</a>}
              </div>
            ))}
          </div>

          {sources.length > 0 && (
            <p className="small muted">使用した情報源: {sources.length} 件（各項目の「出典」から確認できます）</p>
          )}
        </section>
      )}
    </main>
  );
}

const inp: React.CSSProperties = {
  display: "block", marginTop: 4, padding: "0.4rem 0.5rem", background: "#0f1626",
  color: "inherit", border: "1px solid var(--border)", borderRadius: 8, minWidth: 120,
};
const btn: React.CSSProperties = {
  padding: "0.6rem 1rem", background: "var(--accent)", color: "#04121f", border: "none",
  borderRadius: 8, fontWeight: 700, cursor: "pointer", alignSelf: "flex-start",
};
