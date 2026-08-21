import { api, type EventItem } from "../../lib/api";
import { Thumb } from "../../components/SpotCard";

export const dynamic = "force-dynamic";

function EventCard({ e }: { e: EventItem }) {
  const period = e.start_at ? `${e.start_at}${e.end_at && e.end_at !== e.start_at ? ` 〜 ${e.end_at}` : ""}` : "日程未定";
  return (
    <div className="card">
      <Thumb src={e.image_url} alt={e.name} emoji="🎆" />
      <div className="title">{e.name}</div>
      <div className="meta">📅 {period}{e.subcategory ? ` · ${e.subcategory}` : ""}</div>
      {e.description && <div className="small muted">{e.description}</div>}
      {e.official_url && (
        <a className="badge official small" href={e.official_url} target="_blank" rel="noreferrer">公式</a>
      )}
    </div>
  );
}

export default async function EventsPage({
  searchParams,
}: {
  searchParams: Promise<{ upcoming?: string }>;
}) {
  const sp = await searchParams;
  const upcoming = sp.upcoming === "true";
  const events = await api.events(`${upcoming ? "upcoming=true&" : ""}limit=100`);

  return (
    <main>
      <h1>イベント・祭り</h1>
      <div className="tabs">
        <a href="/events" className={!upcoming ? "active" : ""}>すべて</a>
        <a href="/events?upcoming=true" className={upcoming ? "active" : ""}>開催中・近日</a>
      </div>
      <div className="grid">
        {(events ?? []).map((e) => <EventCard key={e.id} e={e} />)}
      </div>
      {(!events || events.length === 0) && (
        <p className="muted">イベントがありません。<code>./scripts/seed.sh</code> を実行してください。</p>
      )}
    </main>
  );
}
