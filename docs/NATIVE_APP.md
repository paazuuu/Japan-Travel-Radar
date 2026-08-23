# Stage 10 — Native App（方針）

11_FUTURE_NATIVE_APP.md に基づく将来計画。PWA（MVP8）で UI と API が安定した後に着手する。
本リポジトリではコードは未実装（実機ビルド・ストア登録は環境外のため）で、方針のみ記す。

## 方針
- **Expo (React Native)** を採用。iOS/Android を単一コードベースで。
- Backend は**既存の `/api/v1` をそのまま利用**（新規APIは基本不要）。
  - 認証は Stage 9 の JWT（`/auth/login` → `Authorization: Bearer`）を流用。
  - お気に入り/プランは `/me/*` を利用（サーバー同期）。
- 地図は `react-native-maps`（iOS: Apple Maps / Android: Google Maps）。
- 状態管理は最小限（TanStack Query 等）で API をキャッシュ。

## リポジトリ構成（予定）
```
mobile/            # Expo アプリ（別ワークスペース）
  app/             # 画面（Home/Map/Ranking/Planner/Saved/Account）
  lib/api.ts       # backend クライアント（Web版と同等のインターフェース）
```

## 移行のしやすさ
- Web(Next.js) の `lib/api.ts` と型定義をほぼ再利用可能（fetch ベース）。
- 画面構成は PWA と同一（Home/Map/Ranking/Planner/Saved）。

## 未対応（意図的）
- 課金（本プロジェクトでは行わない）。
- プッシュ通知・ディープリンク等は必要になった時点で追加。
