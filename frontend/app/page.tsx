import { api } from "../lib/api";
import { RankingCard, SpotCard } from "../components/SpotCard";

export const dynamic = "force-dynamic";

// Osaka (Umeda) as the default day-trip origin for MVP.
const OSAKA = { lat: 34.7025, lng: 135.4959 };

function Section({ title, children, href }: { title: string; children: React.ReactNode; href?: string }) {
  return (
    <section>
      <div className="section-head">
        <h2>{title}</h2>
        {href && <a className="small muted" href={href}>もっと見る →</a>}
      </div>
      {children}
    </section>
  );
}

export default async function Home() {
  const [rising, trending, seasonal, food, dayTrip, events] = await Promise.all([
    api.rankings("rising"),
    api.rankings("trending"),
    api.rankings("seasonal"),
    api.rankings("food"),
    api.nearbySpots(OSAKA.lat, OSAKA.lng, 60000),
    api.events("upcoming=true&limit=6"),
  ]);

  const empty = !rising && !trending && !dayTrip;

  return (
    <main>
      <h1>今行く価値のある場所</h1>
      {empty && (
        <p className="muted small">
          データがまだありません。<code>./scripts/seed.sh</code> と
          <code> ./scripts/rank.sh</code> を実行するとランキングが表示されます。
        </p>
      )}

      <Section title="🔥 今日の急上昇" href="/ranking?kind=rising">
        <div className="grid">
          {(rising ?? []).slice(0, 6).map((it, i) => <RankingCard key={it.id} item={it} rank={i + 1} />)}
        </div>
      </Section>

      <Section title="🧭 今週のおすすめ" href="/ranking?kind=trending">
        <div className="grid">
          {(trending ?? []).slice(0, 6).map((it, i) => <RankingCard key={it.id} item={it} rank={i + 1} />)}
        </div>
      </Section>

      <Section title="🚗 大阪から日帰り" href="/map">
        <div className="grid">
          {(dayTrip ?? []).slice(0, 6).map((s) => <SpotCard key={s.id} spot={s} />)}
        </div>
      </Section>

      <Section title="🌸 季節スポット" href="/ranking?kind=seasonal">
        <div className="grid">
          {(seasonal ?? []).slice(0, 6).map((it, i) => <RankingCard key={it.id} item={it} rank={i + 1} />)}
        </div>
      </Section>

      <Section title="🍣 人気グルメ" href="/food">
        <div className="grid">
          {(food ?? []).slice(0, 6).map((it, i) => <RankingCard key={it.id} item={it} rank={i + 1} />)}
        </div>
      </Section>

      <Section title="🎆 開催中・近日のイベント" href="/events">
        <div className="grid">
          {(events ?? []).slice(0, 6).map((e) => (
            <a key={e.id} href="/events" className="card">
              <div className="title">{e.name}</div>
              <div className="meta">📅 {e.start_at ?? "日程未定"}{e.subcategory ? ` · ${e.subcategory}` : ""}</div>
              {e.description && <div className="small muted">{e.description}</div>}
            </a>
          ))}
        </div>
      </Section>
    </main>
  );
}
