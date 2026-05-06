"use client";

import { motion, useReducedMotion } from "motion/react";
import { Sparkles } from "lucide-react";

import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/hooks/useThemeTokens";

/**
 * Приветственное сообщение на пустом экране.
 *
 * Никаких кликабельных карточек-затравок (см. spec, Section 6.5):
 * пользователь сам формулирует, что у него происходит.
 *
 * Тексты согласованы с философией Кайроса: «не замена», «рядом»,
 * без обесценивания и без «всё будет хорошо».
 */
export function EmptyState() {
  const t = useThemeTokens();
  const prefersReduced = useReducedMotion();

  return (
    <div className="flex flex-col items-center justify-center text-center max-w-xl mx-auto py-12 px-4">
      <motion.div
        className={cn(
          "size-16 rounded-full flex items-center justify-center mb-6 shadow-2xl backdrop-blur-md border",
          t.glassSidebar,
          t.textMain,
        )}
        animate={prefersReduced ? undefined : { y: [0, -8, 0] }}
        transition={prefersReduced ? undefined : { duration: 4, repeat: Infinity, ease: "easeInOut" }}
        aria-hidden="true"
      >
        <Sparkles className="size-8" />
      </motion.div>
      <h2
        className={cn(
          "text-2xl md:text-3xl font-semibold tracking-tight mb-4",
          t.textMain,
        )}
      >
        Здесь можно говорить как есть
      </h2>
      <p className={cn("text-base leading-relaxed max-w-md", t.textMuted)}>
        Я — Кайрос. Не психолог и не врач, но я рядом, если тебе тяжело.
        Расскажи, что у тебя сейчас, — постараюсь помочь. Если это срочно,
        нажми SOS в правом верхнем углу.
      </p>
    </div>
  );
}
