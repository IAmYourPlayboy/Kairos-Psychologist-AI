"use client";

/**
 * Модалка первого визита — Слой 1 дисклеймера + 3 чекбокса согласия.
 *
 * Показывается ОДИН раз при первом заходе пользователя. Без всех трёх
 * галочек пользователь не может писать боту (в чате блокируется input).
 *
 * Состояние «модалка показана» хранится в localStorage. После принятия
 * согласий отправляется на бекенд POST /api/consent.
 *
 * ФЗ-152 ст.10: данные о состоянии — спецкатегория ПДн, требует
 * отдельного явного согласия.
 */

import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/Dialog";
import { Button } from "@/components/ui/Button";
import { useSession } from "@/hooks/useSession";

const CONSENT_GIVEN_KEY = "kairos.consent_v1_given";

const CONSENT_ITEMS: Array<{
  id: ConsentType;
  label: string;
  link: { href: string; text: string };
}> = [
  {
    id: "terms_of_service",
    label: "Принимаю",
    link: { href: "/legal/terms", text: "Пользовательское соглашение" },
  },
  {
    id: "data_processing",
    label: "Согласен(на) на обработку данных о моём состоянии (ст. 10 ФЗ-152) — это",
    link: { href: "/legal/privacy", text: "Политика конфиденциальности" },
  },
  {
    id: "research_anonymized",
    label: "Согласен(на) на использование обезличенных данных для улучшения сервиса —",
    link: { href: "/legal/consent", text: "Информированное согласие" },
  },
];

type ConsentType = "terms_of_service" | "data_processing" | "research_anonymized";

export function FirstVisitModal() {
  const { guestId } = useSession();
  const [open, setOpen] = useState(false);
  const [checked, setChecked] = useState<Record<ConsentType, boolean>>({
    terms_of_service: false,
    data_processing: false,
    research_anonymized: false,
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const given = localStorage.getItem(CONSENT_GIVEN_KEY);
    if (!given) {
      setOpen(true);
    }
  }, []);

  const allChecked = Object.values(checked).every(Boolean);

  const handleToggle = (id: ConsentType) => {
    setChecked((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleAccept = async () => {
    if (!allChecked || !guestId || submitting) return;

    setSubmitting(true);
    try {
      const response = await fetch("/api/consent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          guest_id: guestId,
          consents: CONSENT_ITEMS.map((item) => ({
            consent_type: item.id,
            document_version: "1.0",
          })),
        }),
      });

      if (!response.ok) {
        // Бекенд может быть недоступен в dev — записываем флаг локально
        // и не блокируем чат. При следующем заходе модалка не появится.
        console.warn("Consent endpoint failed, storing locally");
      }

      localStorage.setItem(CONSENT_GIVEN_KEY, "1");
      setOpen(false);
    } catch (e) {
      // Сеть упала — всё равно сохраняем локально, чтобы не зацикливать
      console.warn("Failed to submit consent:", e);
      localStorage.setItem(CONSENT_GIVEN_KEY, "1");
      setOpen(false);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={() => {}}>
      {/* НЕЛЬЗЯ закрыть кликом снаружи или Esc — только через кнопку */}
      <DialogContent
        className="bg-white dark:bg-neutral-900 max-w-2xl max-h-[90vh] overflow-y-auto"
        onPointerDownOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle className="text-xl flex items-center gap-2">
            <AlertTriangle className="size-5 text-amber-500" />
            Прежде чем мы начнём
          </DialogTitle>
          <DialogDescription className="text-sm">
            Кайрос — это инструмент первой психологической помощи.
            Прочитайте короткое описание и отметьте согласия — без этого
            закон не позволяет нам обрабатывать ваши данные.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 text-sm">
          <div className="rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 p-3 text-amber-900 dark:text-amber-200">
            <strong>Кайрос не заменяет врача или психолога.</strong>{" "}
            В острой ситуации звоните 112 или на телефоны доверия.
            Сервис помогает справиться с моментом, но не лечит и не
            ставит диагнозы.
          </div>

          <p>
            Мы серьёзно относимся к вашей приватности:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-neutral-700 dark:text-neutral-300">
            <li>Серверы в России (требование ФЗ-152).</li>
            <li>
              Имена, телефоны, email и адреса автоматически удаляются
              из сохраняемых текстов в течение 15 минут.
            </li>
            <li>В любой момент можно посмотреть и удалить всё, что мы знаем.</li>
            <li>Никакой рекламы и продажи данных третьим лицам.</li>
          </ul>

          <div className="space-y-3 pt-2">
            {CONSENT_ITEMS.map((item) => (
              <label
                key={item.id}
                className="flex items-start gap-2 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={checked[item.id]}
                  onChange={() => handleToggle(item.id)}
                  className="mt-0.5 size-4 rounded border-neutral-400"
                />
                <span>
                  {item.label}{" "}
                  <a
                    href={item.link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline text-accent-600 hover:text-accent-700"
                  >
                    {item.link.text}
                  </a>
                </span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-2 pt-4">
          <Button
            onClick={handleAccept}
            disabled={!allChecked || submitting}
            className="w-full"
          >
            {submitting ? "Сохраняем…" : "Согласен(на), продолжить"}
          </Button>
          <p className="text-xs text-neutral-500 text-center">
            Если не готовы — закройте вкладку. Без всех трёх галочек
            закон запрещает нам работать с вашими данными.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
