"use client";

/**
 * Карточка результата ASQ.
 *
 * Тон-сообщений зависит от interpretation:
 * - negative: лёгкое подтверждение «спасибо, рад что прямо сейчас всё стабильно»
 * - non_acute_positive: внимательное «есть моменты, давай побудем рядом»
 *   + кризисные контакты как опция
 * - acute_positive: серьёзное «прямо сейчас лучше позвонить» + контакты явно
 *
 * ВАЖНО: ASQ-positive автоматически активирует override risk_level=immediate
 * на бекенде (см. ADR-1). Поэтому пользователь увидит CrisisPanel в следующих
 * сообщениях. Здесь мы только информируем о результате.
 *
 * Не показываем числовой score — пользователю это не информативно. Показываем
 * категорию словами + действия.
 */

import { AlertCircle, CheckCircle2, Info, PhoneCall } from "lucide-react";

import { Button } from "@/components/ui/Button";
import type { ASQResult } from "@/lib/screening";

interface ScreeningResultCardProps {
  result: ASQResult;
  onClose: () => void;
}

// Кризисные контакты для отображения прямо в карточке (в случае positive).
// Дублирование с backend `crisis/contacts.py` — намеренно: если бекенд
// упал, эти контакты должны быть доступны.
const CRISIS_CONTACTS = [
  { label: "112", phone: "112", description: "Единый номер экстренных служб" },
  {
    label: "8-800-2000-122",
    phone: "8-800-2000-122",
    description: "Детский телефон доверия (анонимно, до 18 лет)",
  },
  {
    label: "8-800-100-49-94",
    phone: "8-800-100-49-94",
    description: "«Помощь рядом» (до 25 лет)",
  },
  {
    label: "8-800-700-84-60",
    phone: "8-800-700-84-60",
    description: "Линия «0-24» (утрата, насилие, суицид)",
  },
];

export function ScreeningResultCard({
  result,
  onClose,
}: ScreeningResultCardProps) {
  if (result.interpretation === "negative") {
    return (
      <div className="space-y-4">
        <div className="flex items-start gap-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 p-3">
          <CheckCircle2 className="size-5 text-emerald-600 dark:text-emerald-400 flex-none mt-0.5" />
          <div className="text-sm text-emerald-900 dark:text-emerald-100">
            <p className="font-medium">Спасибо, что ответил(а) честно.</p>
            <p className="mt-1 text-emerald-800 dark:text-emerald-200">
              По твоим ответам прямо сейчас острых сигналов нет. Это
              хороший знак. Если что-то изменится — я буду здесь.
            </p>
          </div>
        </div>
        <Button onClick={onClose} className="w-full">
          Продолжить разговор
        </Button>
      </div>
    );
  }

  // Both non_acute_positive and acute_positive: показываем контакты
  const isAcute = result.interpretation === "acute_positive";

  return (
    <div className="space-y-4">
      <div
        className={
          "flex items-start gap-3 rounded-xl border p-3 "
          + (isAcute
            ? "bg-crisis-50 dark:bg-crisis-950/30 border-crisis-300 dark:border-crisis-800"
            : "bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900")
        }
      >
        {isAcute ? (
          <AlertCircle className="size-5 text-crisis-600 dark:text-crisis-400 flex-none mt-0.5" />
        ) : (
          <Info className="size-5 text-amber-600 dark:text-amber-400 flex-none mt-0.5" />
        )}
        <div className="text-sm">
          <p className="font-medium">
            {isAcute
              ? "Сейчас тебе нужен живой человек."
              : "Спасибо, что доверился(ась)."}
          </p>
          <p className="mt-1 text-neutral-700 dark:text-neutral-300">
            {isAcute
              ? (
                  "По твоим ответам сейчас есть мысли, с которыми один(одна) "
                  + "лучше не оставаться. Ниже — номера, по которым отвечают "
                  + "люди, обученные помогать. Бесплатно, анонимно, круглосуточно."
                )
              : (
                  "По твоим ответам видно, что в последнее время непросто. "
                  + "Я остаюсь здесь — мы можем продолжить разговор. И, если "
                  + "захочешь, ниже номера, где можно поговорить с живым человеком."
                )}
          </p>
        </div>
      </div>

      {/* Кризисные контакты */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-neutral-600 dark:text-neutral-400 uppercase tracking-wide">
          Кому можно позвонить
        </p>
        <ul className="space-y-2">
          {CRISIS_CONTACTS.map((c) => (
            <li key={c.label}>
              <a
                href={`tel:${c.phone.replace(/[^0-9+]/g, "")}`}
                aria-label={`Позвонить ${c.phone.split("").join(" ")}`}
                className="flex items-start gap-3 rounded-lg border border-warm-300 dark:border-neutral-700 hover:bg-warm-100/50 dark:hover:bg-neutral-800/50 p-3 transition-colors"
              >
                <PhoneCall className="size-4 text-accent-600 dark:text-accent-400 flex-none mt-0.5" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium">{c.label}</div>
                  <div className="text-xs text-neutral-600 dark:text-neutral-400">
                    {c.description}
                  </div>
                </div>
              </a>
            </li>
          ))}
        </ul>
      </div>

      <Button onClick={onClose} className="w-full" variant="outline">
        Я понял(а), продолжим разговор
      </Button>

      <p className="text-xs text-neutral-500 text-center">
        Я по-прежнему здесь. Бот не заменяет живого специалиста, но
        и не уходит, пока ты пишешь.
      </p>
    </div>
  );
}
