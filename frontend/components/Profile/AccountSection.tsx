"use client";

/**
 * Секция профиля: данные аккаунта + действия (logout, delete).
 *
 * Для гостя — ссылки на login/register вместо профиля.
 * Для залогиненного — email + действия.
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { LogOut, Shield, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/Button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/Dialog";
import { useAuth } from "@/hooks/useAuth";
import { ApiClientError, deleteAccount } from "@/lib/auth";

export function AccountSection() {
  const router = useRouter();
  const { user, status, logout } = useAuth();
  const [busy, setBusy] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (status === "loading") {
    return (
      <div className="rounded-2xl border border-warm-200/60 dark:border-neutral-800/60 bg-white/40 dark:bg-neutral-900/40 backdrop-blur-md p-6 text-sm text-neutral-500">
        Загружаем аккаунт…
      </div>
    );
  }

  if (status === "unauthenticated" || !user) {
    return (
      <section className="rounded-2xl border border-warm-200/60 dark:border-neutral-800/60 bg-white/40 dark:bg-neutral-900/40 backdrop-blur-md p-6 space-y-3">
        <h2 className="text-lg font-semibold">Сейчас ты как гость</h2>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          История чатов и досье хранятся локально в этом браузере. Если
          почистишь cookies — всё пропадёт. Создай аккаунт, чтобы
          сохранить и иметь доступ с других устройств.
        </p>
        <div className="flex gap-2 pt-2">
          <Link href="/auth/register">
            <Button>Создать аккаунт</Button>
          </Link>
          <Link href="/auth/login">
            <Button variant="outline">Войти</Button>
          </Link>
        </div>
      </section>
    );
  }

  const handleLogout = async (everywhere: boolean) => {
    setBusy(true);
    try {
      await logout(everywhere);
      router.push("/chat");
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Не удалось выйти",
      );
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    setBusy(true);
    setError(null);
    try {
      await deleteAccount();
      // Soft-delete: сервер пометил аккаунт на удаление через 7 дней,
      // отозвал все refresh-токены. Перебрасываем на /chat — пользователь
      // станет гостем, при попытке войти обратно увидит баннер «отменить
      // удаление».
      window.location.href = "/chat";
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Не удалось запланировать удаление",
      );
      setBusy(false);
      setConfirmDelete(false);
    }
  };

  return (
    <section className="rounded-2xl border border-warm-200/60 dark:border-neutral-800/60 bg-white/40 dark:bg-neutral-900/40 backdrop-blur-md p-6 space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Аккаунт</h2>
        <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
          {user.email}
          {user.display_name ? ` · ${user.display_name}` : ""}
        </p>
        <p className="text-xs text-neutral-500 mt-1">
          Создан: {new Date(user.created_at).toLocaleDateString("ru-RU")}
        </p>
      </div>

      <div className="flex flex-wrap gap-2 pt-2">
        <Button
          variant="outline"
          onClick={() => handleLogout(false)}
          disabled={busy}
        >
          <LogOut className="size-4" />
          Выйти
        </Button>
        <Button
          variant="outline"
          onClick={() => handleLogout(true)}
          disabled={busy}
        >
          <Shield className="size-4" />
          Выйти со всех устройств
        </Button>
        <Button
          variant="destructive"
          onClick={() => setConfirmDelete(true)}
          disabled={busy}
        >
          <Trash2 className="size-4" />
          Удалить аккаунт
        </Button>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-lg bg-crisis-50 dark:bg-crisis-950/30 border border-crisis-200 dark:border-crisis-900 px-3 py-2 text-sm text-crisis-800 dark:text-crisis-200"
        >
          {error}
        </div>
      )}

      <Dialog
        open={confirmDelete}
        onOpenChange={(open) => !busy && setConfirmDelete(open)}
      >
        <DialogContent className="bg-white dark:bg-neutral-900 max-w-md">
          <DialogHeader>
            <DialogTitle>Удалить аккаунт?</DialogTitle>
            <DialogDescription>
              Через <strong>7 дней</strong> будут удалены:
            </DialogDescription>
          </DialogHeader>
          <ul className="text-sm space-y-1 text-neutral-700 dark:text-neutral-300 list-disc pl-5">
            <li>Аккаунт и все вспомогательные данные</li>
            <li>Досье — что Кайрос знает о тебе</li>
            <li>Согласия и refresh-токены</li>
          </ul>
          <p className="text-xs text-neutral-500">
            Сообщения уже обезличены и могут остаться для обучения сервиса
            (без связи с тобой). В течение этих 7 дней ты можешь
            залогиниться обратно и отменить удаление.
          </p>
          <p className="text-xs text-neutral-500">
            Подписки автоматически не отменяются — отмени их отдельно,
            если они есть.
          </p>
          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              onClick={() => setConfirmDelete(false)}
              disabled={busy}
              className="flex-1"
            >
              Отмена
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={busy}
              className="flex-1"
            >
              {busy ? "Запросим…" : "Да, запросить удаление"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </section>
  );
}
