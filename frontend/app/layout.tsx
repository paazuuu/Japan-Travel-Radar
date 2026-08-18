import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { BottomNav, PwaRegister } from "../components/Pwa";

export const metadata: Metadata = {
  title: "Japan Travel AI Radar",
  description: "今行く価値のある場所を発見する旅行インテリジェンス基盤",
  manifest: "/manifest.webmanifest",
  appleWebApp: { capable: true, statusBarStyle: "black-translucent", title: "Travel Radar" },
  icons: { icon: "/icon.svg", apple: "/icon.svg" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0b1120",
};

const links = [
  ["/", "🏠 Home"],
  ["/ranking", "📈 Ranking"],
  ["/map", "🗺 Map"],
  ["/food", "🍣 Food"],
  ["/planner", "🧳 Planner"],
  ["/saved", "⭐ Saved"],
  ["/admin", "⚙ Admin"],
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <header className="nav">
          <div className="nav-inner">
            <a href="/" className="brand">🧭 Travel Radar</a>
            {links.map(([href, label]) => (
              <a key={href} href={href} className="link">{label}</a>
            ))}
          </div>
        </header>
        <div className="container">{children}</div>
        <BottomNav />
        <PwaRegister />
      </body>
    </html>
  );
}
