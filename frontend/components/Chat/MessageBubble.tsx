"use client";

import HumanTypingEffect from "./HumanTypingEffect";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
  onTypingComplete?: () => void;
}

/**
 * Пузырь сообщения в чате
 *
 * Для сообщений бота использует HumanTypingEffect для "живой" печати
 */
export default function MessageBubble({
  role,
  content,
  isStreaming = false,
  onTypingComplete,
}: MessageBubbleProps) {
  const isBot = role === "assistant";

  return (
    <div
      className={`flex ${isBot ? "justify-start" : "justify-end"} mb-4`}
    >
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isBot
            ? "bg-gray-100 text-gray-900"
            : "bg-blue-600 text-white"
        }`}
      >
        {isBot && !isStreaming ? (
          // Бот: используем HumanTypingEffect для "живой" печати
          <HumanTypingEffect
            text={content}
            onComplete={onTypingComplete}
            speed="normal"
          />
        ) : (
          // Пользователь или streaming: обычный текст
          <span className="whitespace-pre-wrap">{content}</span>
        )}
      </div>
    </div>
  );
}
