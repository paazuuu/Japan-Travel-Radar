"use client";

import { useEffect } from "react";

export function PwaRegister() {
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        /* registration is best-effort */
      });
    }
  }, []);
  return null;
}

const items: [string, string, string][] = [
  ["/", "🏠", "Home"],
  ["/map", "🗺", "Map"],
  ["/ranking", "📈", "Ranking"],
  ["/planner", "🧳", "Planner"],
  ["/saved", "⭐", "Saved"],
];

export function BottomNav() {
  return (
    <nav className="bottom-nav" aria-label="モバイルナビ">
      {items.map(([href, icon, label]) => (
        <a key={href} href={href}>
          <span className="bn-icon">{icon}</span>
          <span className="bn-label">{label}</span>
        </a>
      ))}
    </nav>
  );
}
