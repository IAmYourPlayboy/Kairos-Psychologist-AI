"use client";

import { useState } from "react";
import { motion } from "motion/react";
import { ThumbsDown, ThumbsUp } from "lucide-react";

import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/hooks/useThemeTokens";
import type { FeedbackEventType } from "@/lib/types";

interface MessageFeedbackProps {
  messageId: string;
  onFeedback: (event: FeedbackEventType, messageId: string) => Promise<void> | void;
}

/**
 * Thumbs up/down под каждым ответом бота. Ключевой сигнал для data flywheel.
 *
 * После клика — заменяется на тихое «Спасибо». Повторно нажать нельзя.
 * API идентичен прошлой версии.
 */
export default function MessageFeedback({
  messageId,
  onFeedback,
}: MessageFeedbackProps) {
  const t = useThemeTokens();
  const [submitted, setSubmitted] = useState<"up" | "down" | null>(null);

  const handleClick = async (kind: "up" | "down") => {
    if (submitted) return;
    setSubmitted(kind);
    const event: FeedbackEventType = kind === "up" ? "thumbs_up" : "thumbs_down";
    try {
      await onFeedback(event, messageId);
    } catch {
      // тихо игнорируем
    }
  };

  if (submitted) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className={cn("text-xs mt-1 ml-2 select-none", t.textMuted)}
        aria-live="polite"
      >
        {submitted === "up"
          ? "Спасибо, что отметил."
          : "Спасибо, я учту это."}
      </motion.div>
    );
  }

  return (
    <div className="flex items-center gap-1 mt-1 ml-2">
      <button
        type="button"
        onClick={() => handleClick("up")}
        aria-label="Это сообщение помогло"
        className={cn(
          "p-1.5 rounded-lg transition-all",
          t.textMuted,
          t.btnHover,
        )}
      >
        <ThumbsUp className="size-3.5" />
      </button>
      <button
        type="button"
        onClick={() => handleClick("down")}
        aria-label="Это сообщение не помогло"
        className={cn(
          "p-1.5 rounded-lg transition-all",
          t.textMuted,
          t.btnHover,
        )}
      >
        <ThumbsDown className="size-3.5" />
      </button>
    </div>
  );
}
