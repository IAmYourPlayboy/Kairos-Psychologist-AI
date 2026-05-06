"use client";

import { motion } from "motion/react";

import HumanTypingEffect from "./HumanTypingEffect";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/hooks/useThemeTokens";

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
  timestamp?: string;
}

/**
 * Пузырь сообщения в чате.
 *
 * Стиль: асимметричные радиусы (как в мессенджерах), glassmorphism для бота,
 * сплошной accent-цвет для пользователя.
 *
 * Анимация появления: spring с разных сторон (юзер — справа, бот — слева).
 */
export default function MessageBubble({
  role,
  content,
  animateTyping = true,
  onTypingComplete,
  timestamp,
}: MessageBubbleProps) {
  const t = useThemeTokens();
  const isBot = role === "assistant";

  return (
    <motion.div
      layout
      initial={{
        opacity: 0,
        scale: 0.7,
        y: 30,
        x: isBot ? -20 : 20,
      }}
      animate={{ opacity: 1, scale: 1, y: 0, x: 0 }}
      transition={{
        type: "spring",
        stiffness: 380,
        damping: 26,
      }}
      className={cn(
        "flex items-end gap-2 mb-3",
        isBot ? "justify-start" : "justify-end",
      )}
      style={{ transformOrigin: isBot ? "bottom left" : "bottom right" }}
    >
      <div
        className={cn(
          "relative max-w-[85%] sm:max-w-[75%] px-4 py-2.5 text-[15px] leading-[1.45] break-words shadow-sm",
          isBot ? "rounded-[20px] rounded-bl-[4px]" : "rounded-[20px] rounded-br-[4px] font-medium",
          isBot ? t.msgAi : t.msgUser,
        )}
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
        {timestamp && (
          <span className="block text-[10px] font-medium opacity-60 mt-1 text-right">
            {timestamp}
          </span>
        )}
      </div>
    </motion.div>
  );
}
