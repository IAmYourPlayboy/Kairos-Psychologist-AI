"use client";

import type { CrisisContact, CrisisLevel } from "@/lib/types";

interface CrisisInlineCardProps {
  level: CrisisLevel;
  contacts: CrisisContact[];
}

/**
 * Карточка кризисных контактов внутри ленты сообщений.
 * Показывается под ответом бота, если crisis_level != normal.
 *
 * Цвета карточки зависят от уровня — мягкие при elevated, ярче при immediate.
 */
export default function CrisisInlineCard({
  level,
  contacts,
}: CrisisInlineCardProps) {
  if (level === "normal" || contacts.length === 0) return null;

  const headers: Record<Exclude<CrisisLevel, "normal">, string> = {
    elevated: "На всякий случай — телефоны помощи",
    high: "Если станет тяжело, позвони сюда",
    immediate: "Прямо сейчас позвони сюда",
  };

  const colorClass: Record<Exclude<CrisisLevel, "normal">, string> = {
    elevated: "border-warm-300 bg-warm-100",
    high: "border-crisis-300 bg-crisis-50",
    immediate: "border-crisis-500 bg-crisis-100",
  };

  const styledLevel = level as Exclude<CrisisLevel, "normal">;

  return (
    <div
      className={`rounded-xl border-2 p-3 my-2 max-w-[80%] ${colorClass[styledLevel]} animate-fade-in`}
    >
      <div className="text-sm font-semibold text-warm-900 mb-2">
        {headers[styledLevel]}
      </div>
      <ul className="space-y-1.5">
        {contacts.slice(0, 3).map((c) => (
          <li key={c.phone} className="text-sm">
            <a
              href={`tel:${c.phone.replace(/[^\d+]/g, "")}`}
              className="block hover:bg-white/50 rounded px-2 py-1 transition-colors"
            >
              <span className="font-bold text-accent-700">{c.phone}</span>
              <span className="text-warm-700"> — {c.name}</span>
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
