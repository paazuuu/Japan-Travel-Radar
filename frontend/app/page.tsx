async function getBackendHealth() {
  const base = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${base}/health`, { cache: "no-store" });
    if (!res.ok) return { status: "unreachable" as const };
    return (await res.json()) as {
      status: string;
      database: boolean;
      postgis: boolean;
      postgis_version: string | null;
    };
  } catch {
    return { status: "unreachable" as const };
  }
}

export default async function Home() {
  const health = await getBackendHealth();

  return (
    <main style={{ maxWidth: 720, margin: "0 auto" }}>
      <h1>Japan Travel AI Radar</h1>
      <p>今行く価値のある場所を発見する旅行インテリジェンス基盤（MVP0）。</p>

      <section
        style={{
          marginTop: "2rem",
          padding: "1rem 1.25rem",
          borderRadius: 12,
          background: "#111827",
          border: "1px solid #1f2937",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Backend Health</h2>
        <pre style={{ whiteSpace: "pre-wrap" }}>
          {JSON.stringify(health, null, 2)}
        </pre>
      </section>
    </main>
  );
}
