"use client";

import { useEffect, useState } from "react";
import { browserBase, type Spot } from "../../lib/api";

interface Drafts {
  xiaohongshu: Record<string, any>;
  wechat: { 标题: string; 正文: string[] };
  video_script: { 标题: string; scenes: { time: string; type: string; text: string }[]; note: string };
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card" style={{ marginBottom: "0.75rem" }}>
      <div className="title">{title}</div>
      {children}
    </div>
  );
}

export default function ContentPage() {
  const [spots, setSpots] = useState<Spot[]>([]);
  const [spotId, setSpotId] = useState<string>("");
  const [drafts, setDrafts] = useState<Drafts | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const preset = new URLSearchParams(window.location.search).get("spot");
    fetch(`${browserBase()}/api/v1/spots?limit=200`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : []))
      .then((data: Spot[]) => {
        setSpots(data);
        setSpotId(preset || data[0]?.id || "");
      })
      .catch(() => setError("スポット一覧を取得できません（seedが必要）。"));
  }, []);

  async function generate() {
    if (!spotId) return;
    setLoading(true); setError(null); setDrafts(null);
    try {
      const res = await fetch(`${browserBase()}/api/v1/content/chinese`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ spot_id: spotId }),
      });
      if (!res.ok) { setError(`生成に失敗 (${res.status})`); return; }
      const data = await res.json();
      setDrafts(data.drafts);
    } catch (e: any) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>中国語コンテンツ生成</h1>
      <p className="small muted">
        DBの事実だけを使い、簡体字の下書きを生成します。<b>自動公開はしません</b>（各プラットフォーム規約の確認と人間レビューが必要）。
      </p>

      <div className="card" style={{ flexDirection: "row", gap: "0.6rem", alignItems: "center", flexWrap: "wrap" }}>
        <select value={spotId} onChange={(e) => setSpotId(e.target.value)}
                style={{ padding: "0.4rem", background: "#0f1626", color: "inherit", border: "1px solid var(--border)", borderRadius: 8, minWidth: 200 }}>
          {spots.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <button onClick={generate} disabled={loading || !spotId}
                style={{ padding: "0.5rem 1rem", background: "var(--accent)", color: "#04121f", border: "none", borderRadius: 8, fontWeight: 700, cursor: "pointer" }}>
          {loading ? "生成中…" : "3種類を生成"}
        </button>
      </div>

      {error && <p className="muted small">{error}</p>}

      {drafts && (
        <div style={{ marginTop: "1rem" }}>
          <h2>📕 小红书</h2>
          <Section title={drafts.xiaohongshu["标题"]}>
            {["地点", "为什么值得去", "交通", "预算", "推荐时间", "拍照位置", "美食", "注意事项"].map((k) => (
              <div key={k} className="small"><b>{k}:</b> {String(drafts.xiaohongshu[k] ?? "")}</div>
            ))}
            <div className="tagrow" style={{ marginTop: 6 }}>
              {(drafts.xiaohongshu["标签"] as string[] || []).map((t) => <span key={t} className="badge">{t}</span>)}
            </div>
          </Section>

          <h2>📗 微信公众号</h2>
          <Section title={drafts.wechat["标题"]}>
            {drafts.wechat["正文"].map((p, i) => <p key={i} className="small">{p}</p>)}
          </Section>

          <h2>🎬 60秒動画台本</h2>
          <Section title={drafts.video_script["标题"]}>
            {drafts.video_script.scenes.map((sc) => (
              <div key={sc.time} className="small"><b>{sc.time}</b>（{sc.type}）: {sc.text}</div>
            ))}
            <div className="small muted" style={{ marginTop: 6 }}>{drafts.video_script.note}</div>
          </Section>

          <p className="badge ref">下書き — 公開前に人間レビュー必須</p>
        </div>
      )}
    </main>
  );
}
