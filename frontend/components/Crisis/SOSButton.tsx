"use client";

import type { CrisisLevel } from "@/lib/types";

interface SOSButtonProps {
  crisisLevel: CrisisLevel;
  onClick: () => void;
}

/**
 * Кнопка SOS в шапке.
 * Всегда видна. Пульсирует при crisis_level != normal.
 *
 * Цвета:
 * - normal:    приглушённый (но кликабельный)
 * - elevated:  тёплый (привлекает внимание мягко)
 * - high:      красный с пульсацией
 * - immediate: яркий красный с быстрой пульсацией
 */
export default function SOSButton({ crisisLevel, onClick }: SOSButtonProps) {
  const styles: Record<CrisisLevel, string> = {
    normal: "bg-warm-200 hover:bg-warm-300 text-warm-700",
    elevated: "bg-crisis-200 hover:bg-crisis-300 text-crisis-800",
    high: "bg-crisis-400 hover:bg-crisis-500 text-white animate-pulse-slow",
    immediate: "bg-crisis-500 hover:bg-crisis-600 text-white animate-pulse",
  };

  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-4 py-2 font-semibold text-sm transition-colors ${styles[crisisLevel]}`}
      aria-label="Открыть кризисные контакты"
    >
      SOS
    </button>
  );
}
