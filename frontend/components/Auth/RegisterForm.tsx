"use client";

/**
 * Форма регистрации.
 *
 * Логика consents:
 * - При монтировании проверяем `GET /api/consent?guest_id=...`.
 *   - Если у guest_id уже есть все 3 — показываем компактный режим
 *     (только email/password/displayName + один общий чекбокс «подтверждаю»).
 *   - Если нет — показываем все 3 чекбокса согласия (как в FirstVisitModal).
 *
 * После успеха — редирект на /chat.
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { useSession } from "@/hooks/useSession";
import { ApiClientError, getConsentStatus } from "@/lib/auth";
import type { ConsentItem, ConsentType } from "@/lib/auth";

const ALL_CONSENTS: Array<{
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

export function RegisterForm() {
  const router = useRouter();
  const { register } = useAuth();
  const { guestId } = useSession();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");

  // Consents: либо «уже есть как у гостя» (1 чекбокс), либо все 3
  const [hasGuestConsents, setHasGuestConsents] = useState<boolean | null>(null);
  const [checked, setChecked] = useState<Record<ConsentType, boolean>>({
    terms_of_service: false,
    data_processing: false,
    research_anonymized: false,
  });
  // Чекбокс компактного режима
  const [confirmCompact, setConfirmCompact] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Проверяем статус consents у гостя один раз при монтировании
  useEffect(() => {
    if (!guestId) {
      setHasGuestConsents(false);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const status = await getConsentStatus(guestId);
        if (!cancelled) {
          setHasGuestConsents(status.has_all_required);
        }
      } catch {
        if (!cancelled) setHasGuestConsents(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [guestId]);

  const allFullChecked = Object.values(checked).every(Boolean);
  const consentsReady = hasGuestConsents ? confirmCompact : allFullChecked;

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Пароль должен быть минимум 8 символов");
      return;
    }
    if (!consentsReady) {
      setError("Чтобы продолжить, нужно принять согласия");
      return;
    }

    setSubmitting(true);
    try {
      // Если у гостя уже есть consents — отправляем пустой массив,
      // бекенд их мигрирует. Иначе — все 3.
      const consentsToSend: ConsentItem[] = hasGuestConsents
        ? []
        : ALL_CONSENTS.map((c) => ({ consent_type: c.id }));

      await register({
        email,
        password,
        displayName: displayName.trim() || undefined,
        guestId,
        consents: consentsToSend,
      });
      router.push("/chat");
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.status === 409) {
          setError("Этот email уже зарегистрирован");
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

  // Пока проверяем consent статус — показываем нейтральный спиннер
  if (hasGuestConsents === null) {
    return (
      <div className="text-sm text-neutral-500 text-center py-8">
        Загрузка…
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <label htmlFor="reg-email" className="block text-sm font-medium">
          Email
        </label>
        <input
          id="reg-email"
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
        <label htmlFor="reg-password" className="block text-sm font-medium">
          Пароль
        </label>
        <input
          id="reg-password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          maxLength={128}
          disabled={submitting}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-lg border border-warm-300 bg-white/70 dark:bg-neutral-900/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent-400"
          placeholder="минимум 8 символов"
        />
      </div>

      <div className="space-y-1.5">
        <label htmlFor="reg-name" className="block text-sm font-medium">
          Псевдоним (необязательно)
        </label>
        <input
          id="reg-name"
          type="text"
          autoComplete="nickname"
          maxLength={100}
          disabled={submitting}
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          className="w-full rounded-lg border border-warm-300 bg-white/70 dark:bg-neutral-900/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent-400"
          placeholder="как тебя называть"
        />
      </div>

      {/* Согласия */}
      {hasGuestConsents ? (
        <div className="space-y-2 pt-1">
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Согласия (Соглашение, обработка данных, исследования) уже даны
            при первом визите. Они переедут с твоим аккаунтом.
          </p>
          <label className="flex items-start gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={confirmCompact}
              onChange={(e) => setConfirmCompact(e.target.checked)}
              className="mt-0.5 size-4 rounded border-neutral-400"
            />
            <span>
              Подтверждаю создание аккаунта и сохранение моей истории.
            </span>
          </label>
        </div>
      ) : (
        <div className="space-y-2 pt-1">
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Чтобы создать аккаунт — прими три согласия (это требование ФЗ-152
            для данных о состоянии):
          </p>
          {ALL_CONSENTS.map((item) => (
            <label
              key={item.id}
              className="flex items-start gap-2 text-sm cursor-pointer"
            >
              <input
                type="checkbox"
                checked={checked[item.id]}
                onChange={() =>
                  setChecked((prev) => ({ ...prev, [item.id]: !prev[item.id] }))
                }
                className="mt-0.5 size-4 rounded border-neutral-400"
              />
              <span>
                {item.label}{" "}
                <Link
                  href={item.link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent-600 hover:text-accent-700 underline"
                >
                  {item.link.text}
                </Link>
              </span>
            </label>
          ))}
        </div>
      )}

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
        disabled={submitting || !email || !password || !consentsReady}
        className="w-full"
      >
        {submitting ? "Создаём аккаунт…" : "Создать аккаунт"}
      </Button>

      <p className="text-center text-sm text-neutral-600 dark:text-neutral-400">
        Уже есть аккаунт?{" "}
        <Link
          href="/auth/login"
          className="text-accent-600 hover:text-accent-700 underline"
        >
          Войти
        </Link>
      </p>
    </form>
  );
}
