"use client";

import { useEffect, useState } from "react";
import { isFavorite, pushRecent, toggleFavorite } from "../lib/store";

export function SpotActions({ id, name }: { id: string; name: string }) {
  const [fav, setFav] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    pushRecent({ id, name });
    setFav(isFavorite(id));
  }, [id, name]);

  async function share() {
    const url = typeof window !== "undefined" ? window.location.href : "";
    const data = { title: name, text: `${name} — Japan Travel AI Radar`, url };
    try {
      if (navigator.share) {
        await navigator.share(data);
      } else {
        await navigator.clipboard.writeText(url);
        setMsg("リンクをコピーしました");
        setTimeout(() => setMsg(null), 2000);
      }
    } catch {
      /* user cancelled */
    }
  }

  return (
    <div className="tagrow" style={{ margin: "0.5rem 0" }}>
      <button
        className={`fav ${fav ? "on" : ""}`}
        onClick={() => setFav(toggleFavorite({ id, name }))}
      >
        {fav ? "★ お気に入り済み" : "☆ お気に入り"}
      </button>
      <button className="fav" onClick={share}>🔗 共有</button>
      {msg && <span className="small muted" style={{ alignSelf: "center" }}>{msg}</span>}
    </div>
  );
}
