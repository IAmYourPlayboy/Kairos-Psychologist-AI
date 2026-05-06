"use client";

import { motion } from "motion/react";

import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/hooks/useThemeTokens";

/**
 * Индикатор «бот думает» — три точки с пульсацией.
 * Стилизован под glassmorphism пузырь бота.
 */
export default function TypingIndicator() {
  const t = useThemeTokens();

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2 }}
      className="flex justify-start mb-3"
      role="status"
      aria-label="Бот печатает ответ"
    >
      <div
        className={cn(
          "rounded-[20px] rounded-bl-[4px] px-4 py-3 inline-flex items-center gap-1.5",
          t.msgAi,
        )}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-50 animate-bounce [animation-delay:-0.3s]" />
        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-50 animate-bounce [animation-delay:-0.15s]" />
        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-50 animate-bounce" />
      </div>
    </motion.div>
  );
}
