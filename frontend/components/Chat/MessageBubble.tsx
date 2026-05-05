"use client";

import HumanTypingEffect from "./HumanTypingEffect";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  /**
   * Анимировать печать (для бота).
   * По умолчанию true — для свежих сообщений.
   * Для сообщений из истории / при перезагрузке — передавать false.
   */
  animateTyping?: boolean;
  onTypingComplete?: () => void;
}

/**
 * Пузырь сообщения в чате.
 *
 * Цвета подобраны под палитру Кайроса (warm + accent):
 * - Бот: тёплый бежевый фон (как лист бумаги)
 * - Пользователь: акцентный синий (доверие, безопасность)
 *
 * Для бота используется HumanTypingEffect — анимация «живой» печати
 * с паузами после знаков препинания.
 */
export default function MessageBubble({
  role,
  content,
  animateTyping = true,
  onTypingComplete,
}: MessageBubbleProps) {
  const isBot = role === "assistant";

  return (
    <div className={`flex ${isBot ? "justify-start" : "justify-end"} mb-3`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 leading-relaxed ${
          isBot
            ? "bg-warm-100 text-warm-900 rounded-bl-sm"
            : "bg-accent-500 text-white rounded-br-sm"
        }`}
      >
        {isBot && animateTyping ? (
          <HumanTypingEffect
            text={content}
            onComplete={onTypingComplete}
            speed="normal"
          />
        ) : (
          <span className="whitespace-pre-wrap break-words">{content}</span>
        )}
      </div>
    </div>
  );
}
