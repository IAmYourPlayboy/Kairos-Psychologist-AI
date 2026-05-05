"use client";

/**
 * Индикатор «бот думает» — три точки с пульсацией.
 * Отображается пока ждём ответ от /api/chat.
 */
export default function TypingIndicator() {
  return (
    <div
      className="flex justify-start mb-4 animate-fade-in"
      role="status"
      aria-label="Бот печатает ответ"
    >
      <div className="bg-warm-100 rounded-2xl px-4 py-3 inline-flex items-center gap-1">
        <span className="w-2 h-2 bg-warm-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
        <span className="w-2 h-2 bg-warm-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
        <span className="w-2 h-2 bg-warm-500 rounded-full animate-bounce" />
      </div>
    </div>
  );
}
