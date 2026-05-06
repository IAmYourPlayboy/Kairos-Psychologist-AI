"use client";

import { motion, useReducedMotion } from "motion/react";
import { AlertTriangle, Phone } from "lucide-react";

import { cn } from "@/lib/cn";
import { spellPhoneForAria, toTelHref } from "@/lib/phoneUtils";
import { useTheme } from "@/hooks/useTheme";
import type { CrisisContact, CrisisLevel } from "@/lib/types";

interface CrisisInlineCardProps {
  level: CrisisLevel;
  contacts: CrisisContact[];
}

/**
 * Карточка кризисных контактов внутри ленты сообщений.
 * Появляется под ответом бота при crisis_level != normal.
 *
 * Стиль: rounded-2xl, прозрачный crisis-цвет, мягкая анимация появления.
 */
export default function CrisisInlineCard({
  level,
  contacts,
}: CrisisInlineCardProps) {
  const { isDark } = useTheme();
  const shouldReduceMotion = useReducedMotion();

  if (level === "normal" || contacts.length === 0) return null;

  const headers: Record<Exclude<CrisisLevel, "normal">, string> = {
    elevated: "На всякий случай — телефоны помощи",
    high: "Если станет тяжело, позвони сюда",
    immediate: "Прямо сейчас позвони сюда",
  };

  const colorClass: Record<Exclude<CrisisLevel, "normal">, string> = {
    elevated: isDark
      ? "border-amber-400/30 bg-amber-500/10 text-amber-100"
      : "border-warm-300 bg-warm-100/80 text-warm-900",
    high: isDark
      ? "border-crisis-400/40 bg-crisis-500/15 text-crisis-50"
      : "border-crisis-300 bg-crisis-50 text-crisis-900",
    immediate: isDark
      ? "border-crisis-400/60 bg-crisis-500/25 text-crisis-50"
      : "border-crisis-500 bg-crisis-100 text-crisis-900",
  };

  const styledLevel = level as Exclude<CrisisLevel, "normal">;

  return (
    <motion.div
      initial={shouldReduceMotion ? false : { opacity: 0, y: 10, scale: 0.97 }}
      animate={shouldReduceMotion ? { opacity: 1, y: 0, scale: 1 } : { opacity: 1, y: 0, scale: 1 }}
      transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3, ease: "easeOut" }}
      className={cn(
        "rounded-2xl border-2 p-3 my-2 max-w-[80%] backdrop-blur-md",
        colorClass[styledLevel],
      )}
    >
      <div className="flex items-center gap-2 mb-2 text-sm font-semibold">
        <AlertTriangle className="size-4" />
        {headers[styledLevel]}
      </div>
      <ul className="space-y-1.5">
        {contacts.slice(0, 3).map((c) => (
          <li key={c.phone}>
            <a
              href={`tel:${toTelHref(c.phone)}`}
              aria-label={`Позвонить ${c.name}: ${spellPhoneForAria(c.phone)}`}
              className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-white/20 transition-colors text-sm"
            >
              <Phone className="size-3.5 opacity-70" />
              <span className="font-bold">{c.phone}</span>
              <span className="opacity-80">— {c.name}</span>
            </a>
          </li>
        ))}
      </ul>
    </motion.div>
  );
}
