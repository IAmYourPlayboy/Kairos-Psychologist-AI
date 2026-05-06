"use client";

import { useState } from "react";
import { motion } from "motion/react";

import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/hooks/useThemeTokens";
import type { FeedbackEventType } from "@/lib/types";

interface SessionFeedbackProps {
  onSubmit: (event: FeedbackEventType) => Promise<void> | void;
  onSkip?: () => void;
}

/**
 * Карточка обратной связи по сессии. Показывается при «Завершить сессию».
 *
 * Три варианта: felt_better / no_change / felt_worse.
 * После выбора — благодарность и закрытие.
 */
export default function SessionFeedback({
  onSubmit,
  onSkip,
}: SessionFeedbackProps) {
  const t = useThemeTokens();
  const [submitted, setSubmitted] = useState<FeedbackEventType | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleClick = async (event: FeedbackEventType) => {
    if (submitted || isSubmitting) return;
    setIsSubmitting(true);
    try {
      await onSubmit(event);
      setSubmitted(event);
    } catch {
      // тихо
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="my-6 mx-auto max-w-md"
      >
        <Card className={cn(t.glassPanel, "p-4 text-center")}>
          <p className={cn("text-sm", t.textMain)}>
            Спасибо. Это помогает мне учиться.
          </p>
        </Card>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="my-6 mx-auto max-w-md"
    >
      <Card className={cn(t.glassPanel)}>
        <CardContent className="p-5">
          <p className={cn("text-sm mb-4 text-center", t.textMain)}>
            Как ты сейчас, после нашего разговора?
          </p>
          <div className="flex flex-col sm:flex-row gap-2">
            <Button
              disabled={isSubmitting}
              onClick={() => handleClick("felt_better")}
              variant="ghost"
              size="sm"
              className={cn(
                "flex-1",
                "bg-accent-100/60 hover:bg-accent-200/80 text-accent-900",
                "dark:bg-accent-500/20 dark:hover:bg-accent-500/30 dark:text-accent-50",
              )}
            >
              Стало легче
            </Button>
            <Button
              disabled={isSubmitting}
              onClick={() => handleClick("no_change")}
              variant="ghost"
              size="sm"
              className={cn(
                "flex-1",
                "bg-warm-200/60 hover:bg-warm-300/80 text-warm-900",
                "dark:bg-white/10 dark:hover:bg-white/20 dark:text-white",
              )}
            >
              Не уверен
            </Button>
            <Button
              disabled={isSubmitting}
              onClick={() => handleClick("felt_worse")}
              variant="ghost"
              size="sm"
              className={cn(
                "flex-1",
                "bg-crisis-50 hover:bg-crisis-100 text-crisis-900",
                "dark:bg-crisis-500/20 dark:hover:bg-crisis-500/30 dark:text-crisis-50",
              )}
            >
              Хуже
            </Button>
          </div>
          {onSkip && (
            <button
              type="button"
              onClick={onSkip}
              className={cn(
                "block mx-auto mt-3 text-xs transition-colors",
                t.textMuted,
              )}
            >
              Пропустить
            </button>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
