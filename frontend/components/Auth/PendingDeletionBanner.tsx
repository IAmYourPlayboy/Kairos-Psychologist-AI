"use client";

/**
 * Баннер «удаление аккаунта запланировано».
 *
 * Показывается если у залогиненного пользователя стоит
 * `deletion_scheduled_at`. Даёт кнопку «отменить удаление» и
 * счётчик «осталось X дней».
 *
 * Рендерится в AppShell поверх всего контента, чтобы пользователь
 * видел его независимо от страницы.
 */

import { useState } from "react";
import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { request } from "@/lib/api";

const MS_PER_DAY = 86_400_000;

export function PendingDeletionBanner() {
  const { user, status, reload } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (status !== "authenticated" || !user || !user.deletion_scheduled_at) {
    return null;
  }

  const scheduledAt = new Date(user.deletion_scheduled_at);
  const daysLeft = Math.max(
    0,
    Math.ceil((scheduledAt.getTime() - Date.now()) / MS_PER_DAY),
  );

  const handleCancel = async () => {
    setBusy(true);
    setError(null);
    try {
      await request<unknown, { ok: boolean; was_scheduled: boolean }>(
        "/api/auth/me/cancel-deletion",
        { method: "POST" },
      );
      // Перезагрузим user из /me — deletion_scheduled_at должен стать null.
      await reload();
    } catch {
      setError("Не получилось отменить. Попробуй ещё раз.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      role="alert"
      className="sticky top-0 z-overlay bg-crisis-100 dark:bg-crisis-950 border-b border-crisis-300 dark:border-crisis-900 px-4 py-2.5 text-sm"
    >
      <div className="mx-auto max-w-5xl flex flex-wrap items-center gap-3 text-crisis-900 dark:text-crisis-100">
        <AlertTriangle className="size-4 shrink-0" />
        <span className="flex-1 min-w-[200px]">
          Аккаунт будет удалён{" "}
          {daysLeft > 0 ? (
            <strong>через {daysLeft} {pluralizeDays(daysLeft)}</strong>
          ) : (
            <strong>в ближайшее время</strong>
          )}
          . Передумал?
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={handleCancel}
          disabled={busy}
          className="border-crisis-400 hover:bg-crisis-200 dark:hover:bg-crisis-900"
        >
          {busy ? "Отменяем…" : "Отменить удаление"}
        </Button>
        {error && (
          <span className="text-xs basis-full text-crisis-700 dark:text-crisis-300">
            {error}
          </span>
        )}
      </div>
    </div>
  );
}

function pluralizeDays(n: number): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod100 >= 11 && mod100 <= 14) return "дней";
  if (mod10 === 1) return "день";
  if (mod10 >= 2 && mod10 <= 4) return "дня";
  return "дней";
}
