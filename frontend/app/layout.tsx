import type { Metadata, Viewport } from "next";
import { Golos_Text } from "next/font/google";

import { AppShell } from "@/components/Layout/AppShell";
import { KairosProviders } from "@/components/Layout/KairosProviders";
import { ThemeScript } from "@/components/Layout/ThemeScript";

import "./globals.css";

const golos = Golos_Text({
  subsets: ["cyrillic", "latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-golos",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Кайрос — первая психологическая помощь",
  description:
    "Сервис первой психологической помощи. Не заменяет психолога — заполняет пустоту, где психолога нет рядом.",
  keywords: [
    "психологическая помощь",
    "кризис",
    "поддержка",
    "первая помощь",
    "AI",
  ],
  authors: [{ name: "Kairos Team" }],
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className={golos.variable} suppressHydrationWarning>
      <head>
        <ThemeScript />
      </head>
      <body className="font-sans antialiased">
        <KairosProviders>
          <AppShell>{children}</AppShell>
        </KairosProviders>
      </body>
    </html>
  );
}
