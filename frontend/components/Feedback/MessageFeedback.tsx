"use client";

import { useState } from "react";

import type { FeedbackEventType } from "@/lib/types";

/**
 * Кнопки обратной связи под каждым ответом бота.
 *
 * Это самый ценный сигнал для data flywheel:
 * - thumbs_up   → ответ помог
 * - thumbs_down → ответ не зашёл
 *
 * После клика кнопки заменяются на «Спасибо» (тихо, без модалок)
 * и больше не показываются — повторно нажать нельзя.
 *
 * Расположение: справа под пузырём бота, очень тонкий вес.
 * Не должно мешать чтению.
 */
interface MessageFeedbackProps {
  messageId: string;
  onFeedback: (event: FeedbackEventType, messageId: string) => Promise<void> | void;
}

export default function MessageFeedback({
  messageId,
  onFeedback,
}: MessageFeedbackProps) {
  const [submitted, setSubmitted] = useState<"up" | "down" | null>(null);

  const handleClick = async (kind: "up" | "down") => {
    if (submitted) return;
    setSubmitted(kind);
    const event: FeedbackEventType =
      kind === "up" ? "thumbs_up" : "thumbs_down";
    try {
      await onFeedback(event, messageId);
    } catch {
      // Если не отправилось — оставим как есть (кнопки не вернутся).
      // Это сознательно: не хотим напрягать пользователя ретраями.
    }
  };

  if (submitted) {
    return (
      <div
        className="text-xs text-warm-500 mt-1 ml-2 select-none"
        aria-live="polite"
      >
        {submitted === "up"
          ? "Спасибо, что отметил."
          : "Спасибо, я учту это."}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1 mt-1 ml-2">
      <button
        type="button"
        onClick={() => handleClick("up")}
        aria-label="Это сообщение помогло"
        className="text-warm-400 hover:text-warm-700 transition-colors p-1 rounded hover:bg-warm-100"
      >
        {/* SVG: thumbs up */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M7 10v12" />
          <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H7v-9a4 4 0 0 1 4-4 1 1 0 0 0 1-1V4a2 2 0 0 1 4 0c0 .76-.21 1.43-.55 2z" />
        </svg>
      </button>
      <button
        type="button"
        onClick={() => handleClick("down")}
        aria-label="Это сообщение не помогло"
        className="text-warm-400 hover:text-warm-700 transition-colors p-1 rounded hover:bg-warm-100"
      >
        {/* SVG: thumbs down */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M17 14V2" />
          <path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H17v9a4 4 0 0 1-4 4 1 1 0 0 0-1 1v3a2 2 0 0 1-4 0c0-.76.21-1.43.55-2z" />
        </svg>
      </button>
    </div>
  );
}
