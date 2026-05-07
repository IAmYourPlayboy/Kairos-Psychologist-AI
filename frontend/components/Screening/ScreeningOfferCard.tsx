"use client";

/**
 * Inline-карточка в чате: предложение пройти ASQ.
 *
 * Появляется когда `useShouldOfferASQ` вернул true. Имеет 2 действия:
 * - «Пройти» → открывает ASQDialog
 * - «Может позже» → отмечает в backend (frequency cap, 7 дней) + локально
 *
 * После прохождения ASQ карточка пропадает из чата (управляет ChatContainer
 * через флаг dismissed).
 */

import { Stethoscope } from "lucide-react";

import { Button } from "@/components/ui/Button";

interface ScreeningOfferCardProps {
  onAccept: () => void;
  onDismiss: () => void;
  busy?: boolean;
}

export function ScreeningOfferCard({
  onAccept,
  onDismiss,
  busy = false,
}: ScreeningOfferCardProps) {
  return (
    <div
      role="region"
      aria-label="Предложение пройти короткий опросник"
      className="my-4 mx-auto max-w-lg rounded-2xl border border-accent-200/70 dark:border-accent-900/60 bg-accent-50/60 dark:bg-accent-950/40 backdrop-blur-md p-4 shadow-sm"
    >
      <div className="flex items-start gap-3">
        <div className="flex-none mt-0.5">
          <div className="size-9 rounded-full bg-accent-100 dark:bg-accent-900 flex items-center justify-center">
            <Stethoscope className="size-5 text-accent-700 dark:text-accent-300" />
          </div>
        </div>
        <div className="flex-1 min-w-0 space-y-2">
          <h3 className="text-sm font-semibold">
            Хочешь пройти 4 коротких вопроса?
          </h3>
          <p className="text-sm text-neutral-700 dark:text-neutral-300">
            Это валидированный опросник от NIH (ASQ). Поможет мне точнее
            понять, насколько серьёзная ситуация прямо сейчас. Займёт меньше
            минуты. Отвечать честно — это для тебя, а не для меня.
          </p>
          <div className="flex gap-2 pt-1">
            <Button
              size="sm"
              onClick={onAccept}
              disabled={busy}
            >
              Пройти
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={onDismiss}
              disabled={busy}
            >
              Может позже
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
