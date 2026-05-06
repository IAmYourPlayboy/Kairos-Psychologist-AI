"use client";

import { Toaster } from "sonner";

import { Background } from "@/components/Layout/Background";
import { FloatingButtons } from "@/components/Layout/FloatingButtons";
import { RightDock } from "@/components/Layout/RightDock";
import { Sidebar } from "@/components/Layout/Sidebar";
import { useTheme } from "@/hooks/useTheme";

/**
 * Корневой shell приложения.
 *
 * Phase 2: добавлен слой Background (wallpaper + overlay).
 * Phase 2.11: добавлен RightDock (ThemeToggle + Avatar + TipCard).
 * Phase 3: добавлены Sidebar (история бесед) и FloatingButtons (настройки + тоггл).
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

      <div className="relative z-10 flex h-full w-full">
        <Sidebar />
        <FloatingButtons />
        <main className="flex-1 flex flex-col h-full w-full relative overflow-hidden">
          {children}
        </main>
        <RightDock />
      </div>
    </div>
  );
}
