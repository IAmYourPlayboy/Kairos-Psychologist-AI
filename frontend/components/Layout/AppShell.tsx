"use client";

import { Toaster } from "sonner";

import { Background } from "@/components/Layout/Background";
import { useTheme } from "@/hooks/useTheme";

/**
 * Корневой shell приложения.
 *
 * Phase 2: добавлен слой Background (wallpaper + overlay).
 * В Phase 3 — Sidebar и RightDock.
 *
 * Фон задаётся через Background компонент с next/image и useWallpaper.
 * children — рендерит контент конкретной страницы (chat / profile / settings).
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const { isDark } = useTheme();

  return (
    <div className="relative flex h-[100dvh] w-full overflow-hidden font-sans">
      <Toaster theme={isDark ? "dark" : "light"} position="top-center" />
      <Background />
      <main className="relative z-10 flex h-full w-full">
        {children}
      </main>
    </div>
  );
}
