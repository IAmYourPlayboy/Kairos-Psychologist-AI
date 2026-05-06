"use client";

import { useTheme } from "@/hooks/useTheme";

/**
 * Темовые токены: единая точка маппинга isDark → набор Tailwind классов.
 *
 * Порт из Figma Make AppContext.tsx::useThemeTokens с адаптацией под
 * нашу палитру (warm/accent/crisis) для светлой темы.
 *
 * Используй так:
 *   const t = useThemeTokens();
 *   <div className={cn("rounded-xl p-4", t.glassPanel)}>...</div>
 */
export function useThemeTokens() {
  const { isDark } = useTheme();
  return {
    overlay: isDark ? "bg-black/50" : "bg-white/20",

    glassSidebar: isDark
      ? "bg-black/30 border-white/10 backdrop-blur-[16px]"
      : "bg-white/60 border-white/40 backdrop-blur-md shadow-sm",
    glassPanel: isDark
      ? "bg-black/40 border-white/10 backdrop-blur-2xl"
      : "bg-white/70 border-white/60 backdrop-blur-2xl shadow-xl",

    textMain: isDark ? "text-white" : "text-warm-900",
    textMuted: isDark ? "text-white/60" : "text-warm-700",

    btnHover: isDark
      ? "hover:bg-white/20 hover:text-white"
      : "hover:bg-warm-900/5 hover:text-warm-900",
    divider: isDark ? "bg-white/10" : "bg-warm-900/10",

    btnPrimary: isDark
      ? "bg-white text-black hover:bg-white/80"
      : "bg-accent-700 text-white hover:bg-accent-800 shadow-md",

    // Юзер-пузырь — единый accent-500 синий в обеих темах. Раньше в тёмной
    // теме был белый (bg-white text-black), что создавало диссонанс между
    // темами. Унификация даёт более согласованный визуальный язык.
    msgUser: "bg-accent-500 text-white shadow-md",
    msgAi: isDark
      ? "bg-white/10 backdrop-blur-xl border border-white/10 text-white shadow-md"
      : "bg-white/85 backdrop-blur-xl border border-warm-200 text-warm-900 shadow-sm",

    inputWrapper: isDark
      ? "bg-white/10 border border-white/20 focus-within:bg-white/15 focus-within:ring-2 focus-within:ring-white/30"
      : "bg-white border border-warm-200 focus-within:ring-2 focus-within:ring-accent-400/30 shadow-xl",

    floatingBtn: isDark
      ? "bg-white/10 hover:bg-white/20 text-white shadow-[0_0_15px_rgba(0,0,0,0.5)] border border-white/20"
      : "bg-white/95 hover:bg-warm-50 text-warm-900 shadow-md border border-warm-200",

    tipCard: isDark
      ? "bg-gradient-to-br from-amber-500/20 to-orange-500/10 border border-amber-400/30 text-amber-50"
      : "bg-gradient-to-br from-amber-50 to-orange-100/80 border border-amber-300/60 text-amber-900",
    tipIcon: isDark
      ? "text-amber-300 bg-amber-500/20 border border-amber-400/20"
      : "text-amber-600 bg-amber-200/60 border border-amber-300",
    tipCloseBtn: isDark
      ? "text-amber-200/50 hover:text-amber-200 hover:bg-amber-500/30"
      : "text-amber-600 hover:text-amber-800 hover:bg-amber-300/50",
  };
}
