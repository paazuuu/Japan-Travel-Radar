"use client";

import { useEffect, useState } from "react";
import {
  getFavorites, getPlans, getRecent, removePlan,
  type SavedPlan, type SavedSpot,
} from "../../lib/store";

export default function SavedPage() {
  const [favorites, setFavorites] = useState<SavedSpot[]>([]);
  const [recent, setRecent] = useState<SavedSpot[]>([]);
  const [plans, setPlans] = useState<SavedPlan[]>([]);

  useEffect(() => {
    setFavorites(getFavorites());
    setRecent(getRecent());
    setPlans(getPlans());
  }, []);

  function drop(id: string) {
    removePlan(id);
    setPlans(getPlans());
  }

  const SpotList = ({ list }: { list: SavedSpot[] }) =>
    list.length === 0 ? (
      <p className="muted small">まだありません。</p>
    ) : (
      <div className="grid">
        {list.map((s) => (
          <a key={s.id} href={`/spots/${s.id}`} className="card">
            <div className="title">{s.name}</div>
          </a>
        ))}
      </div>
    );

  return (
    <main>
      <h1>保存済み</h1>

      <h2>⭐ お気に入り</h2>
      <SpotList list={favorites} />

      <h2>🕘 最近見たスポット</h2>
      <SpotList list={recent} />

      <h2>🧳 保存した旅行プラン</h2>
      {plans.length === 0 ? (
        <p className="muted small">プランはまだありません。<a href="/planner">プランを作成</a>して保存できます。</p>
      ) : (
        <div className="grid">
          {plans.map((p) => (
            <div key={p.id} className="card">
              <a href={`/planner?plan=${p.id}`} className="title">{p.origin} のプラン</a>
              <div className="small muted">{p.summary}</div>
              <button className="fav" onClick={() => drop(p.id)}>削除</button>
            </div>
          ))}
        </div>
      )}

      <p className="small muted" style={{ marginTop: "1.5rem" }}>
        ※ お気に入り・履歴・保存プランはこの端末のブラウザに保存されます（アカウント機能は将来対応）。
      </p>
    </main>
  );
}
