"use client";

import { useState } from "react";

import type { FeedbackEventType } from "@/lib/types";

/**
 * Большая карточка обратной связи по всей сессии.
 *
 * Показывается когда:
 * - Пользователь нажал кнопку «Завершить сессию» (или появится по триггеру в Блоке 11+)
 * - В будущем: после N сообщений или при долгой паузе
 *
 * Три варианта:
 * - Стало легче  → felt_better  (главный позитивный сигнал)
 * - Не уверен    → no_change    (нейтральный)
 * - Хуже         → felt_worse   (негативный — критично для качества бота)
 *
 * Этот сигнал — главное, что идёт в обучение LoRA на следующих фазах.
 */
interface SessionFeedbackProps {
  onSubmit: (event: FeedbackEventType) => Promise<void> | void;
  onSkip?: () => void;
}

export default function SessionFeedback({
  onSubmit,
  onSkip,
}: SessionFeedbackProps) {
  const [submitted, setSubmitted] = useState<FeedbackEventType | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleClick = async (event: FeedbackEventType) => {
    if (submitted || isSubmitting) return;
    setIsSubmitting(true);
    try {
      await onSubmit(event);
      setSubmitted(event);
    } catch {
      // Тихо игнорируем — пользователь не должен застревать
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="my-6 mx-auto max-w-md p-4 bg-accent-50 border border-accent-200 rounded-xl text-center animate-fade-in">
        <p className="text-warm-800 text-sm">
          Спасибо. Это помогает мне учиться.
        </p>
      </div>
    );
  }

  return (
    <div className="my-6 mx-auto max-w-md p-5 bg-warm-100 border border-warm-200 rounded-xl animate-fade-in">
      <p className="text-warm-800 text-sm mb-4 text-center">
        Как ты сейчас, после нашего разговора?
      </p>
      <div className="flex flex-col sm:flex-row gap-2">
        <button
          type="button"
          disabled={isSubmitting}
          onClick={() => handleClick("felt_better")}
          className="flex-1 px-4 py-2 bg-accent-100 hover:bg-accent-200 text-accent-900 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          Стало легче
        </button>
        <button
          type="button"
          disabled={isSubmitting}
          onClick={() => handleClick("no_change")}
          className="flex-1 px-4 py-2 bg-warm-200 hover:bg-warm-300 text-warm-900 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          Не уверен
        </button>
        <button
          type="button"
          disabled={isSubmitting}
          onClick={() => handleClick("felt_worse")}
          className="flex-1 px-4 py-2 bg-crisis-50 hover:bg-crisis-100 text-crisis-900 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          Хуже
        </button>
      </div>
      {onSkip && (
        <button
          type="button"
          onClick={onSkip}
          className="block mx-auto mt-3 text-xs text-warm-500 hover:text-warm-700 transition-colors"
        >
          Пропустить
        </button>
      )}
    </div>
  );
}
