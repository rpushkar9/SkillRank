import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SkillRank Frontend",
  description: "Next.js frontend for SkillRank semantic search.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
