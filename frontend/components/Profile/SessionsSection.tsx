"use client";

/**
 * Секция «История чатов» на странице профиля.
 *
 * Залогиненный — забираем с сервера через /api/sessions.
 * Гость — пока не показываем (у него история в Sidebar и она локальная).
 *
 * Действия:
 * - Кликнуть → перейти в чат с этой сессией
 * - Корзина → удалить (с подтверждением)
 */

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Trash2, MessageSquare } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { useSession } from "@/hooks/useSession";
import { ApiClientError } from "@/lib/auth";
import {
  deleteServerSession,
  listSessions,
  type SessionSummary,
} from "@/lib/sessions";

const LEVEL_BADGES: Record<string, { label: string; classes: string }> = {
  immediate: {
    label: "Кризис",
    classes: "bg-crisis-100 text-crisis-800 dark:bg-crisis-950 dark:text-crisis-200",
  },
  high: {
    label: "Высокий",
    classes: "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-200",
  },
  elevated: {
    label: "Тревога",
    classes: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200",
  },
  normal: {
    label: "",
    classes: "",
  },
};

export function SessionsSection() {
  const router = useRouter();
  const { status } = useAuth();
  const { switchToSession } = useSession();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status !== "authenticated") return;
    let cancelled = false;
    setLoading(true);
    void (async () => {
      try {
        const data = await listSessions();
        if (!cancelled) setSessions(data);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiClientError ? err.message : "Не удалось загрузить",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [status]);

  if (status !== "authenticated") return null;

  const handleOpen = (s: SessionSummary) => {
    switchToSession(s.id);
    router.push("/chat");
  };

  const handleDelete = async (s: SessionSummary, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Удалить чат «${s.title}»? Это действие нельзя отменить.`)) {
      return;
    }
    try {
      await deleteServerSession(s.id);
      setSessions((prev) => prev.filter((x) => x.id !== s.id));
    } catch (err) {
      alert(err instanceof ApiClientError ? err.message : "Не удалось удалить");
    }
  };

  return (
    <section className="rounded-2xl border border-warm-200/60 dark:border-neutral-800/60 bg-white/40 dark:bg-neutral-900/40 backdrop-blur-md p-6 space-y-3">
      <h2 className="text-lg font-semibold">История чатов</h2>

      {loading && (
        <p className="text-sm text-neutral-500">Загружаем…</p>
      )}

      {error && (
        <p className="text-sm text-crisis-700 dark:text-crisis-300">{error}</p>
      )}

      {!loading && !error && sessions.length === 0 && (
        <p className="text-sm text-neutral-500">
          Чатов пока нет. Начни в{" "}
          <button
            onClick={() => router.push("/chat")}
            className="underline text-accent-600 hover:text-accent-700"
          >
            новой беседе
          </button>
          .
        </p>
      )}

      <ul className="space-y-2">
        {sessions.map((s) => {
          const badge = LEVEL_BADGES[s.crisis_level_max] ?? LEVEL_BADGES.normal;
          const date = new Date(s.last_message_at ?? s.created_at);
          return (
            <li key={s.id}>
              {/* Строка-обёртка — div, а не button: внутри нужна кнопка
                  удаления (Trash2), вложенные <button> невалидны в HTML
                  и ломают hydration. Hover-эффект держим через `group`. */}
              <div className="relative flex items-stretch gap-2 rounded-lg border border-warm-200/60 dark:border-neutral-800/60 hover:bg-warm-100/60 dark:hover:bg-neutral-800/60 transition group">
                {/* Основная кликабельная область — открывает сессию */}
                <button
                  type="button"
                  onClick={() => handleOpen(s)}
                  className="flex-1 min-w-0 text-left flex items-center gap-3 px-3 py-2 rounded-lg"
                >
                  <MessageSquare className="size-4 text-neutral-500 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium truncate">
                        {s.title}
                      </span>
                      {badge.label && (
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded ${badge.classes}`}
                        >
                          {badge.label}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-neutral-500 mt-0.5">
                      {date.toLocaleString("ru-RU", {
                        day: "numeric",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                      {" · "}
                      {s.message_count} сообщ.
                    </div>
                  </div>
                </button>
                {/* Кнопка удаления — отдельно от открытия, не вложена */}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => handleDelete(s, e)}
                  className="shrink-0 mr-1 self-center opacity-0 group-hover:opacity-100 focus-visible:opacity-100 transition-opacity"
                  aria-label={`Удалить чат ${s.title}`}
                >
                  <Trash2 className="size-4 text-crisis-600" />
                </Button>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
