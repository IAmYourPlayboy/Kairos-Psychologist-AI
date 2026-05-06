"use client";

import { Toaster } from "sonner";

import { cn } from "@/lib/cn";
import { useTheme } from "@/hooks/useTheme";

/**
 * Корневой shell приложения.
 *
 * MVP-фаза: только контейнер с фоном и Toaster.
 * В Phase 2 добавим Background, в Phase 3 — Sidebar и RightDock.
 *
 * children — рендерит контент конкретной страницы (chat / profile / settings).
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const { isDark, mounted } = useTheme();

  return (
    <div
      className={cn(
        "relative flex h-[100dvh] w-[100dvw] overflow-hidden font-sans transition-colors duration-700",
        // До маунта рендерим без класса (anti-flash скрипт уже выставил .dark на <html>).
        // После маунта класс контролируется хуком (через .dark на <html>).
        mounted && isDark ? "bg-neutral-950" : "bg-warm-50",
      )}
    >
      <Toaster theme={isDark ? "dark" : "light"} position="top-center" />

      {/* Слой контента */}
      <main className="relative z-10 flex h-full w-full">
        {children}
      </main>
    </div>
  );
}
