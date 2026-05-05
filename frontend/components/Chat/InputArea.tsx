"use client";

import { useEffect, useRef, useState } from "react";

interface InputAreaProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

/**
 * Поле ввода + кнопка отправки.
 *
 * Особенности:
 * - Enter — отправить, Shift+Enter — новая строка.
 * - Автоматически растёт по высоте (до 6 строк).
 * - Блокируется когда disabled=true (бот печатает).
 */
export default function InputArea({
  onSend,
  disabled = false,
  placeholder = "Напиши, что у тебя сейчас...",
}: InputAreaProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Авторазмер высоты textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 144)}px`; // max 144px ≈ 6 строк
  }, [text]);

  function handleSend() {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="border-t border-warm-200 bg-warm-50 px-4 py-3">
      <div className="flex items-end gap-2 max-w-3xl mx-auto">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          disabled={disabled}
          className="flex-1 resize-none rounded-xl border border-warm-300 bg-white px-3 py-2 text-warm-900 placeholder:text-warm-400 focus:outline-none focus:ring-2 focus:ring-accent-400 focus:border-transparent disabled:bg-warm-100 disabled:text-warm-500 disabled:cursor-not-allowed leading-relaxed"
          aria-label="Сообщение"
        />

        <button
          type="button"
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className="rounded-xl bg-accent-500 hover:bg-accent-600 text-white px-4 py-2 font-medium transition-colors disabled:bg-warm-300 disabled:cursor-not-allowed shrink-0"
          aria-label="Отправить"
        >
          ↑
        </button>
      </div>

      <p className="text-xs text-warm-500 mt-2 text-center max-w-3xl mx-auto">
        Это не замена врачу или психологу. В кризисе звони{" "}
        <a href="tel:112" className="underline">
          112
        </a>{" "}
        или{" "}
        <a href="tel:88003334434" className="underline">
          8-800-333-44-34
        </a>
        .
      </p>
    </div>
  );
}
