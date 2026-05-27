import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "video-auto-editor",
  description: "Auto cut-editing dashboard for vlogs and shorts.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
