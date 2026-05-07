"use client";

/**
 * Форма логина (email + пароль).
 *
 * После успеха — редирект на `redirectTo` (по умолчанию /chat).
 * При ошибке — inline-сообщение + сохранение введённого email.
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { ApiClientError } from "@/lib/auth";

interface LoginFormProps {
  /** Куда редиректить после успешного входа. По умолчанию /chat. */
  redirectTo?: string;
}

export function LoginForm({ redirectTo = "/chat" }: LoginFormProps) {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      router.push(redirectTo);
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.status === 401) {
          setError("Неверный email или пароль");
        } else if (err.type === "network") {
          setError("Нет связи с сервером. Проверь интернет.");
        } else {
          setError(err.message);
        }
      } else {
        setError("Что-то пошло не так. Попробуй ещё раз.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <label htmlFor="email" className="block text-sm font-medium">
          Email
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          required
          disabled={submitting}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-lg border border-warm-300 bg-white/70 dark:bg-neutral-900/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent-400"
          placeholder="ты@example.com"
        />
      </div>

      <div className="space-y-1.5">
        <label htmlFor="password" className="block text-sm font-medium">
          Пароль
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          required
          minLength={8}
          disabled={submitting}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-lg border border-warm-300 bg-white/70 dark:bg-neutral-900/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent-400"
          placeholder="минимум 8 символов"
        />
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-lg bg-crisis-50 dark:bg-crisis-950/30 border border-crisis-200 dark:border-crisis-900 px-3 py-2 text-sm text-crisis-800 dark:text-crisis-200"
        >
          {error}
        </div>
      )}

      <Button
        type="submit"
        disabled={submitting || !email || !password}
        className="w-full"
      >
        {submitting ? "Входим…" : "Войти"}
      </Button>

      <p className="text-center text-sm text-neutral-600 dark:text-neutral-400">
        Нет аккаунта?{" "}
        <Link
          href="/auth/register"
          className="text-accent-600 hover:text-accent-700 underline"
        >
          Зарегистрироваться
        </Link>
      </p>
    </form>
  );
}
