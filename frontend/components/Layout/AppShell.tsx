"use client";

import { Toaster } from "sonner";

import { useTheme } from "@/hooks/useTheme";

/**
 * Корневой shell приложения.
 *
 * MVP-фаза: только контейнер с фоном и Toaster.
 * В Phase 2 добавим Background, в Phase 3 — Sidebar и RightDock.
 *
 * Фон задаётся в globals.css через body/dark body — здесь его нет намеренно,
 * чтобы избежать вспышки при pre-hydration (anti-flash скрипт уже выставил
 * .dark на <html> до React).
 *
 * children — рендерит контент конкретной страницы (chat / profile / settings).
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const { isDark } = useTheme();

  return (
    <div
      className="relative flex h-[100dvh] w-full overflow-hidden font-sans"
    >
      <Toaster theme={isDark ? "dark" : "light"} position="top-center" />

      {/* Слой контента */}
      <main className="relative z-10 flex h-full w-full">
        {children}
      </main>
    </div>
  );
}
