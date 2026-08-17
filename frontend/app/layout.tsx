import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Japan Travel AI Radar",
  description: "今行く価値のある場所を発見する旅行インテリジェンス基盤",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body
        style={{
          fontFamily: "system-ui, sans-serif",
          margin: 0,
          padding: "2rem",
          background: "#0b1120",
          color: "#e2e8f0",
        }}
      >
        {children}
      </body>
    </html>
  );
}
