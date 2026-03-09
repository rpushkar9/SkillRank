import type { Metadata } from "next";
import { ThemeProvider } from "next-themes";
import { DottedSurface } from "@/components/ui/dotted-surface";
import "./globals.css";

export const metadata: Metadata = {
  title: "SkillRank",
  description: "Search for AI skills using natural language.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <ThemeProvider attribute="class" defaultTheme="dark" disableTransitionOnChange>
          <DottedSurface />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
