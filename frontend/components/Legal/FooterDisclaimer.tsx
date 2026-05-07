"use client";

/**
 * Footer-disclaimer (Слой 3 из CLAUDE.md).
 *
 * Постоянно видим внизу страницы. Напоминает, что Кайрос — не медицинская
 * услуга. Содержит ссылки на 4 юридические страницы.
 *
 * Дизайн: лёгкий, не кричащий — пользователь должен иметь возможность
 * сосредоточиться на разговоре, но при необходимости найти информацию.
 */

export function FooterDisclaimer() {
  return (
    <footer className="px-4 py-3 text-[11px] text-neutral-500 dark:text-neutral-500 border-t border-neutral-200/60 dark:border-neutral-800/60 bg-white/40 dark:bg-neutral-950/40 backdrop-blur-sm">
      <div className="mx-auto max-w-3xl flex flex-col sm:flex-row items-center justify-between gap-2">
        <p>
          Не является медицинской услугой. В кризисе — звоните 112.
        </p>
        <nav className="flex flex-wrap gap-x-3 gap-y-1 justify-center">
          <a href="/legal/privacy" className="hover:underline">
            Конфиденциальность
          </a>
          <a href="/legal/terms" className="hover:underline">
            Соглашение
          </a>
          <a href="/legal/offer" className="hover:underline">
            Оферта
          </a>
          <a href="/legal/consent" className="hover:underline">
            Согласие
          </a>
        </nav>
      </div>
    </footer>
  );
}
