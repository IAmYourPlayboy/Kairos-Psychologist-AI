import type { Metadata, Viewport } from "next";
import { Golos_Text } from "next/font/google";
import "./globals.css";

// Golos Text — основной шрифт приложения.
// Опции: 400 (regular), 500 (medium), 600 (semibold), 700 (bold).
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
  // Не индексируем во время разработки
  robots: {
    index: false,
    follow: false,
  },
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
    <html lang="ru" className={golos.variable}>
      <body className="font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
