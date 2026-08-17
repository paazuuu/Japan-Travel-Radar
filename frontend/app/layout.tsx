import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Japan Travel AI Radar",
  description: "今行く価値のある場所を発見する旅行インテリジェンス基盤",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

const links = [
  ["/", "🏠 Home"],
  ["/ranking", "📈 Ranking"],
  ["/map", "🗺 Map"],
  ["/food", "🍣 Food"],
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
      </body>
    </html>
  );
}
