"use client";

import { motion, useReducedMotion } from "motion/react";
import { LifeBuoy } from "lucide-react";

import { cn } from "@/lib/cn";
import type { CrisisLevel } from "@/lib/types";

interface SOSButtonProps {
  crisisLevel: CrisisLevel;
  onClick: () => void;
}

/**
 * Кнопка SOS. Всегда видна. Стиль и пульсация зависят от crisisLevel.
 *
 * Поведение НЕ изменилось по сравнению с прошлой версией.
 * Изменился ТОЛЬКО стиль: glassmorphism + lucide-иконка вместо текста "SOS"
 * на нормальном уровне; на crisis-уровнях — красная заливка + текст "SOS".
 */
export default function SOSButton({ crisisLevel, onClick }: SOSButtonProps) {
  const isAlert = crisisLevel === "high" || crisisLevel === "immediate";
  const isElevated = crisisLevel === "elevated";
  const shouldReduceMotion = useReducedMotion();

  const baseClasses =
    "rounded-full font-semibold text-sm transition-all duration-300 shadow-lg backdrop-blur-xl border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-400";

  const stateClasses = (() => {
    if (crisisLevel === "immediate")
      return "bg-crisis-500 hover:bg-crisis-600 text-white border-crisis-400 animate-pulse";
    if (crisisLevel === "high")
      return "bg-crisis-400 hover:bg-crisis-500 text-white border-crisis-300 animate-pulse-slow";
    if (isElevated)
      return "bg-crisis-200/80 hover:bg-crisis-300 text-crisis-900 border-crisis-300/60";
    // normal
    return "bg-white/30 hover:bg-white/50 text-crisis-700 dark:bg-white/15 dark:text-white/90 dark:hover:bg-white/25 border-white/40 dark:border-white/20";
  })();

  return (
    <motion.button
      type="button"
      onClick={onClick}
      aria-label="Открыть кризисные контакты"
      whileHover={shouldReduceMotion ? undefined : { scale: 1.05 }}
      whileTap={shouldReduceMotion ? undefined : { scale: 0.95 }}
      className={cn(
        baseClasses,
        stateClasses,
        isAlert ? "px-4 py-2 flex items-center gap-1.5" : "size-11 flex items-center justify-center",
      )}
    >
      <LifeBuoy className={cn(isAlert ? "size-4" : "size-5")} />
      {isAlert && <span>SOS</span>}
    </motion.button>
  );
}
