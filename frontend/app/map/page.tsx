"use client";

import { useEffect, useRef, useState } from "react";
import { browserBase, type Spot } from "../../lib/api";

// Map provider is fixed to Leaflet + OpenStreetMap for MVP (07: 1社に固定).
const LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
const LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";

function loadLeaflet(): Promise<any> {
  return new Promise((resolve, reject) => {
    const w = window as any;
    if (w.L) return resolve(w.L);
    if (!document.querySelector(`link[href="${LEAFLET_CSS}"]`)) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = LEAFLET_CSS;
      document.head.appendChild(link);
    }
    const script = document.createElement("script");
    script.src = LEAFLET_JS;
    script.onload = () => resolve((window as any).L);
    script.onerror = reject;
    document.body.appendChild(script);
  });
}

const CATEGORIES = ["", "sightseeing", "nature", "onsen", "culture", "event", "gourmet"];

export default function MapPage() {
  const mapEl = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const layerRef = useRef<any>(null);
  const [category, setCategory] = useState("");
  const [count, setCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const L = await loadLeaflet();
        if (cancelled || !mapEl.current) return;
        if (!mapRef.current) {
          mapRef.current = L.map(mapEl.current).setView([34.75, 135.5], 8); // Kansai
          L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap contributors",
            maxZoom: 18,
          }).addTo(mapRef.current);
          layerRef.current = L.layerGroup().addTo(mapRef.current);
        }
        const q = category ? `&category=${category}` : "";
        const res = await fetch(`${browserBase()}/api/v1/spots?limit=200${q}`, { cache: "no-store" });
        const spots: Spot[] = res.ok ? await res.json() : [];
        layerRef.current.clearLayers();
        let n = 0;
        for (const s of spots) {
          if (s.lat == null || s.lng == null) continue;
          n++;
          const score = s.trend_score != null ? `🔥 ${s.trend_score.toFixed(0)}` : "";
          L.marker([s.lat, s.lng])
            .bindPopup(
              `<b>${s.name}</b><br/>${s.category ?? ""} ${score}` +
                `<br/><a href="/spots/${s.id}">詳細 →</a>`
            )
            .addTo(layerRef.current);
        }
        if (!cancelled) setCount(n);
      } catch (e: any) {
        if (!cancelled) setError(String(e));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [category]);

  return (
    <main>
      <div className="section-head">
        <h1>地図</h1>
        <span className="small muted">{count != null ? `${count} スポット` : ""}</span>
      </div>
      <div className="tabs">
        {CATEGORIES.map((c) => (
          <a
            key={c || "all"}
            onClick={() => setCategory(c)}
            className={c === category ? "active" : ""}
            style={{ cursor: "pointer" }}
          >
            {c || "すべて"}
          </a>
        ))}
      </div>
      {error && <p className="muted small">地図データの取得に失敗しました: {error}</p>}
      <div
        ref={mapEl}
        style={{ height: "70vh", minHeight: 360, borderRadius: 12, overflow: "hidden", border: "1px solid var(--border)" }}
      />
      <p className="small muted">地図: Leaflet + OpenStreetMap。ピンをタップで詳細へ。</p>
    </main>
  );
}
