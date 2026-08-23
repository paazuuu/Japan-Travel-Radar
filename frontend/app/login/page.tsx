"use client";

import { useEffect, useState } from "react";
import { browserBase } from "../../lib/api";
import { clearToken, getToken, setToken } from "../../lib/store";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [me, setMe] = useState<{ email: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function loadMe() {
    const token = getToken();
    if (!token) { setMe(null); return; }
    try {
      const res = await fetch(`${browserBase()}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }, cache: "no-store",
      });
      setMe(res.ok ? await res.json() : null);
      if (!res.ok) clearToken();
    } catch { setMe(null); }
  }

  useEffect(() => { loadMe(); }, []);

  async function submit() {
    setBusy(true); setError(null);
    try {
      const res = await fetch(`${browserBase()}/api/v1/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        setError(res.status === 401 ? "メールまたはパスワードが違います" :
                 res.status === 409 ? "このメールは登録済みです" : `失敗 (${res.status})`);
        return;
      }
      setToken((await res.json()).access_token);
      await loadMe();
    } catch (e: any) { setError(String(e)); }
    finally { setBusy(false); }
  }

  if (me) {
    return (
      <main>
        <h1>アカウント</h1>
        <p>ログイン中: <b>{me.email}</b></p>
        <p className="small muted">お気に入り・保存プランがこのアカウントに紐づきます（端末をまたいで同期）。</p>
        <button className="fav" onClick={() => { clearToken(); setMe(null); }}>ログアウト</button>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 420 }}>
      <h1>ログイン / 登録</h1>
      <div className="tabs">
        <a onClick={() => setMode("login")} className={mode === "login" ? "active" : ""} style={{ cursor: "pointer" }}>ログイン</a>
        <a onClick={() => setMode("register")} className={mode === "register" ? "active" : ""} style={{ cursor: "pointer" }}>新規登録</a>
      </div>
      <div className="card" style={{ gap: "0.6rem" }}>
        <input placeholder="メールアドレス" value={email} onChange={(e) => setEmail(e.target.value)} style={inp} />
        <input type="password" placeholder="パスワード" value={password} onChange={(e) => setPassword(e.target.value)} style={inp} />
        <button onClick={submit} disabled={busy || !email || !password} style={btn}>
          {busy ? "処理中…" : mode === "login" ? "ログイン" : "登録"}
        </button>
        {error && <div className="small muted">{error}</div>}
      </div>
      <p className="small muted" style={{ marginTop: "1rem" }}>
        ※ アカウント機能は Stage 9 の基盤です（課金なし）。
      </p>
    </main>
  );
}

const inp: React.CSSProperties = {
  padding: "0.5rem 0.6rem", background: "#0f1626", color: "inherit",
  border: "1px solid var(--border)", borderRadius: 8,
};
const btn: React.CSSProperties = {
  padding: "0.6rem 1rem", background: "var(--accent)", color: "#04121f",
  border: "none", borderRadius: 8, fontWeight: 700, cursor: "pointer",
};
