import { api } from "../../lib/api";

export const dynamic = "force-dynamic";

interface Source { id: string; source_type: string; source_name: string; last_collected_at: string | null; }
interface Run { source_key: string; status: string; fetched: number; inserted: number; updated: number; skipped: number; pruned: number; error_count: number; started_at: string; }
interface Err { source_key: string; error_type: string; message: string; created_at: string; }
interface Stats { spots: number; published_spots: number; restaurants: number; sources: number; analyses: number; trend_scores: number; }

export default async function AdminPage() {
  const [stats, sources, runs, errors] = await Promise.all([
    api.admin<Stats>("stats"),
    api.admin<Source[]>("sources"),
    api.admin<Run[]>("collector-runs?limit=15"),
    api.admin<Err[]>("errors?limit=20"),
  ]);

  return (
    <main>
      <h1>管理</h1>

      <h2>統計</h2>
      {stats ? (
        <div className="grid">
          {Object.entries(stats).map(([k, v]) => (
            <div key={k} className="card"><div className="meta">{k}</div><div className="score" style={{ fontSize: "1.4rem" }}>{v}</div></div>
          ))}
        </div>
      ) : <p className="muted">API未接続</p>}

      <h2>情報源</h2>
      <table className="admin">
        <thead><tr><th>種別</th><th>名称</th><th>最終収集</th></tr></thead>
        <tbody>
          {(sources ?? []).map((s) => (
            <tr key={s.id}><td>{s.source_type}</td><td>{s.source_name}</td><td className="muted">{s.last_collected_at ?? "—"}</td></tr>
          ))}
        </tbody>
      </table>

      <h2>収集ジョブ</h2>
      <table className="admin">
        <thead><tr><th>source</th><th>状態</th><th>取得</th><th>登録</th><th>更新</th><th>スキップ</th><th>削除</th><th>エラー</th><th>開始</th></tr></thead>
        <tbody>
          {(runs ?? []).map((r, i) => (
            <tr key={i}>
              <td>{r.source_key}</td><td>{r.status}</td><td>{r.fetched}</td><td>{r.inserted}</td>
              <td>{r.updated}</td><td>{r.skipped}</td><td>{r.pruned}</td><td>{r.error_count}</td>
              <td className="muted">{r.started_at?.slice(0, 19)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>エラーログ</h2>
      <table className="admin">
        <thead><tr><th>source</th><th>種別</th><th>メッセージ</th><th>時刻</th></tr></thead>
        <tbody>
          {(errors ?? []).map((e, i) => (
            <tr key={i}><td>{e.source_key}</td><td>{e.error_type}</td><td className="muted">{e.message}</td><td className="muted">{e.created_at?.slice(0, 19)}</td></tr>
          ))}
        </tbody>
      </table>
      {!runs && <p className="muted small">Backend API に接続できません。docker compose 起動後に表示されます。</p>}
    </main>
  );
}
