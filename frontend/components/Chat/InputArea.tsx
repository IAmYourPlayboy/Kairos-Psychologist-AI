"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import { ArrowUp } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/hooks/useThemeTokens";

interface InputAreaProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

/**
 * Поле ввода + кнопка отправки.
 *
 * Стиль: glassmorphism rounded-[28px] контейнер, кнопка-стрелка справа.
 * НЕТ голосового ввода (mic) и НЕТ прикрепления файлов на MVP —
 * это лишний функционал для кризисной помощи (см. spec).
 *
 * Особенности:
 * - Enter — отправить, Shift+Enter — новая строка
 * - Авторазмер высоты (до ~6 строк)
 * - Дисклеймер про 112 / 8-800 — внизу под полем
 */
export default function InputArea({
  onSend,
  disabled = false,
  placeholder = "Напиши, что у тебя сейчас...",
}: InputAreaProps) {
  const t = useThemeTokens();
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 144)}px`;
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
    <div className="w-full px-4 sm:px-6 pb-3 sm:pb-4">
      <div className="max-w-3xl mx-auto">
        <div
          className={cn(
            "w-full rounded-[28px] backdrop-blur-2xl flex px-3 py-2 items-end gap-2 transition-all duration-300",
            t.inputWrapper,
          )}
        >
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={1}
            disabled={disabled}
            aria-label="Сообщение"
            className={cn(
              "flex-1 resize-none bg-transparent border-none outline-none text-[15px] py-1.5 px-1 min-w-0 leading-relaxed",
              t.textMain,
              "placeholder:opacity-50",
              disabled && "opacity-50 cursor-not-allowed",
            )}
          />
          <Button
            type="button"
            onClick={handleSend}
            disabled={disabled || !text.trim()}
            aria-label="Отправить"
            size="icon"
            className={cn(
              "size-10 rounded-full shrink-0",
              text.trim() ? cn(t.btnPrimary, "shadow-lg") : "bg-transparent",
              !text.trim() && cn(t.textMuted, t.btnHover),
            )}
          >
            <motion.div
              className="size-full flex items-center justify-center"
              whileHover={text.trim() ? { y: -1, scale: 1.1 } : undefined}
              transition={{ type: "spring", bounce: 0.5 }}
            >
              <ArrowUp className="size-[18px]" />
            </motion.div>
          </Button>
        </div>

        <p
          className={cn(
            "text-[11px] font-medium mt-2 text-center",
            t.textMuted,
          )}
        >
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
    </div>
  );
}
