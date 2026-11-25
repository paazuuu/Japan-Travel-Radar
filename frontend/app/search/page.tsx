import { api } from "../../lib/api";
import { SpotCard } from "../../components/SpotCard";

export const dynamic = "force-dynamic";

const CATEGORIES: [string, string][] = [
  ["", "すべて"],
  ["sightseeing", "観光"],
  ["nature", "自然"],
  ["onsen", "温泉"],
  ["culture", "文化"],
  ["event", "イベント"],
  ["gourmet", "グルメ"],
];

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; category?: string }>;
}) {
  const sp = await searchParams;
  const q = (sp.q ?? "").trim();
  const category = sp.category ?? "";
  const results = q ? await api.search(q, category) : null;
  const href = (c: string) => `/search?q=${encodeURIComponent(q)}${c ? `&category=${c}` : ""}`;

  return (
    <main>
      <h1>スポット検索</h1>
      <form action="/search" method="get" role="search" style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <input
          name="q"
          defaultValue={q}
          placeholder="名前・タグで検索（例: 京都 / 温泉 / 紅葉）"
          aria-label="検索キーワード"
          style={{ flex: 1, padding: "0.55rem 0.8rem", borderRadius: 999, border: "1px solid var(--border)", background: "var(--panel)", color: "var(--text)", fontSize: "1rem" }}
        />
        {category && <input type="hidden" name="category" value={category} />}
        <button type="submit" className="fav">検索</button>
      </form>

      {q && (
        <div className="tabs">
          {CATEGORIES.map(([c, label]) => (
            <a key={c || "all"} href={href(c)} className={c === category ? "active" : ""}>{label}</a>
          ))}
        </div>
      )}

      {!q && <p className="muted">キーワードを入力してください。誤字や一部の文字でも、近い名前・AIタグから関連度順に探します。</p>}
      {q && results === null && <p className="muted">検索に失敗しました。時間をおいて再度お試しください。</p>}
      {q && results && (
        <>
          <p className="small muted">「{q}」の検索結果: {results.length} 件（関連度順）</p>
          <div className="grid">
            {results.map((s) => <SpotCard key={s.id} spot={s} />)}
          </div>
          {results.length === 0 && <p className="muted">該当するスポットがありません。別のキーワードをお試しください。</p>}
        </>
      )}
    </main>
  );
}
