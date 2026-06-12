import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI BizOps Orchestrator",
  description: "BizOps and RevOps workflow diagnosis MVP",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}

