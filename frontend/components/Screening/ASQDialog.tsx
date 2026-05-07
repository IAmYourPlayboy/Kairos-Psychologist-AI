"use client";

/**
 * Модалка прохождения ASQ.
 *
 * Поток:
 * 1. При открытии — загрузить структуру опросника (`GET /api/screening/asq`).
 * 2. Показать вопросы 1–4 (поочерёдно — один на экран).
 * 3. Если хоть один "yes" → задать 5-й (acuity).
 * 4. На submit → `POST /api/screening/asq` → показать результат.
 *
 * Дизайн:
 * - Радио-группа для ответов (yes/no/decline)
 * - Прогресс-индикатор (1/4, 2/4 и т.д.)
 * - Можно вернуться к предыдущему вопросу
 * - Нельзя закрыть модалку случайным кликом извне (ESC/X — можно, на середине
 *   спросим подтверждение в виде alert, потому что данные не сохранены)
 *
 * Вопросы и формулировки приходят с бекенда — не хардкодим на frontend
 * (это **валидированный научный инструмент**, формулировки = source of truth
 * на бекенде, мы только отображаем).
 */

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/Dialog";
import { Button } from "@/components/ui/Button";
import { ScreeningResultCard } from "@/components/Screening/ScreeningResultCard";
import {
  ApiClientError,
  getASQQuestionnaire,
  submitASQ,
  type ASQAnswer,
  type ASQQuestion,
  type ASQResult,
} from "@/lib/screening";

interface ASQDialogProps {
  open: boolean;
  sessionId: string;
  onClose: () => void;
  /** Вызывается с результатом, когда опросник пройден.
   *  Используется ChatContainer чтобы закрыть карточку-приглашение. */
  onCompleted?: (result: ASQResult) => void;
}

const ANSWER_LABELS: Record<ASQAnswer, string> = {
  yes: "Да",
  no: "Нет",
  decline: "Не хочу отвечать",
};

export function ASQDialog({
  open,
  sessionId,
  onClose,
  onCompleted,
}: ASQDialogProps) {
  const [questions, setQuestions] = useState<ASQQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<number, ASQAnswer>>({});
  const [currentIdx, setCurrentIdx] = useState(0);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ASQResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Загрузка структуры при открытии
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    void (async () => {
      try {
        const data = await getASQQuestionnaire();
        if (cancelled) return;
        setQuestions(data.questions);
        setAnswers({});
        setCurrentIdx(0);
        setResult(null);
      } catch (e) {
        if (cancelled) return;
        setError(
          e instanceof ApiClientError
            ? e.message
            : "Не удалось загрузить опросник",
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open]);

  // Разделение core (1-4) и acuity (5)
  const coreQuestions = questions.filter((q) => !q.is_acuity);
  const acuityQuestion = questions.find((q) => q.is_acuity) ?? null;

  // Был ли "yes" на любом из core → надо задать acuity
  const hasAnyYesOnCore = coreQuestions.some(
    (q) => answers[q.id] === "yes",
  );

  // Последовательность вопросов: core + (acuity если нужен)
  const orderedQuestions = hasAnyYesOnCore && acuityQuestion
    ? [...coreQuestions, acuityQuestion]
    : coreQuestions;

  const currentQuestion = orderedQuestions[currentIdx] ?? null;
  const isLastQuestion = currentIdx === orderedQuestions.length - 1;
  const allAnswered = orderedQuestions.every((q) => q.id in answers);

  const handleAnswer = (answer: ASQAnswer) => {
    if (!currentQuestion) return;
    setAnswers((prev) => ({ ...prev, [currentQuestion.id]: answer }));
  };

  const handleNext = () => {
    if (!currentQuestion) return;
    if (!(currentQuestion.id in answers)) return;

    // После 4-го core: если ни одного "yes" — переходим к submit (без acuity)
    // Иначе — продолжаем (next будет acuity)
    if (isLastQuestion) {
      void handleSubmit();
      return;
    }
    setCurrentIdx((idx) => idx + 1);
  };

  const handleBack = () => {
    if (currentIdx > 0) setCurrentIdx((idx) => idx - 1);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const r = await submitASQ(sessionId, answers);
      setResult(r);
      onCompleted?.(r);
    } catch (e) {
      setError(
        e instanceof ApiClientError
          ? e.message
          : "Не удалось отправить ответы. Попробуй ещё раз.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    // Если опросник в процессе и есть ответы — спрашиваем подтверждение
    if (Object.keys(answers).length > 0 && !result) {
      const ok = window.confirm(
        "Прервать опросник? Введённые ответы не сохранятся.",
      );
      if (!ok) return;
    }
    onClose();
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        if (!o) handleClose();
      }}
    >
      <DialogContent className="bg-white dark:bg-neutral-900 max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {result ? "Спасибо за честность" : "ASQ — короткий опросник"}
          </DialogTitle>
          {!result && currentQuestion && (
            <DialogDescription>
              Вопрос {currentIdx + 1} из {orderedQuestions.length}
            </DialogDescription>
          )}
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-8 text-neutral-500">
            <Loader2 className="size-5 animate-spin mr-2" />
            Загружаем…
          </div>
        )}

        {error && !loading && (
          <div
            role="alert"
            className="rounded-lg bg-crisis-50 dark:bg-crisis-950/30 border border-crisis-200 dark:border-crisis-900 px-3 py-2 text-sm text-crisis-800 dark:text-crisis-200"
          >
            {error}
          </div>
        )}

        {result && <ScreeningResultCard result={result} onClose={onClose} />}

        {!loading && !result && currentQuestion && (
          <div className="space-y-4">
            <p className="text-sm text-neutral-800 dark:text-neutral-200 leading-relaxed">
              {currentQuestion.text}
            </p>

            <div className="flex flex-col gap-2">
              {(["yes", "no", "decline"] as ASQAnswer[]).map((opt) => {
                const isSelected = answers[currentQuestion.id] === opt;
                return (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => handleAnswer(opt)}
                    disabled={submitting}
                    className={
                      "text-left px-3 py-2 rounded-lg border text-sm transition-colors "
                      + (isSelected
                        ? "border-accent-500 bg-accent-50 dark:bg-accent-950/40 text-accent-900 dark:text-accent-100"
                        : "border-warm-300 dark:border-neutral-700 hover:bg-warm-100/50 dark:hover:bg-neutral-800/50")
                    }
                  >
                    {ANSWER_LABELS[opt]}
                  </button>
                );
              })}
            </div>

            <div className="flex justify-between gap-2 pt-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleBack}
                disabled={currentIdx === 0 || submitting}
              >
                Назад
              </Button>
              <Button
                size="sm"
                onClick={handleNext}
                disabled={
                  !(currentQuestion.id in answers) || submitting
                }
              >
                {submitting
                  ? "Отправляем…"
                  : isLastQuestion
                  ? (allAnswered ? "Завершить" : "Далее")
                  : "Далее"}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
