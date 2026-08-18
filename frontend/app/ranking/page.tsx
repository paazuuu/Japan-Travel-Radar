import { api } from "../../lib/api";
import { RankingCard } from "../../components/SpotCard";

export const dynamic = "force-dynamic";

const KINDS: [string, string][] = [
  ["trending", "総合"],
  ["rising", "急上昇"],
  ["new", "新着"],
  ["seasonal", "季節"],
  ["popular", "人気"],
  ["food", "食"],
];

export default async function RankingPage({
  searchParams,
}: {
  searchParams: Promise<{ kind?: string; category?: string }>;
}) {
  const sp = await searchParams;
  const kind = KINDS.some((k) => k[0] === sp.kind) ? sp.kind! : "trending";
  const catParam = sp.category ? `&category=${encodeURIComponent(sp.category)}` : "";
  const items = await api.rankings(kind, catParam);

  return (
    <main>
      <h1>ランキング</h1>
      <div className="tabs">
        {KINDS.map(([k, label]) => (
          <a key={k} href={`/ranking?kind=${k}`} className={k === kind ? "active" : ""}>{label}</a>
        ))}
      </div>
      <p className="small muted">
        スコアは日次更新。サンプルや情報源が少ない項目は「参考値」表示です（更新日: {items?.[0]?.score_date ?? "—"}）。
      </p>
      <div className="grid">
        {(items ?? []).map((it, i) => <RankingCard key={it.id} item={it} rank={i + 1} />)}
      </div>
      {(!items || items.length === 0) && <p className="muted">データがありません。scripts/rank.sh を実行してください。</p>}
    </main>
  );
}
