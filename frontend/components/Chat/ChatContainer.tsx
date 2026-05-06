"use client";

import { useEffect, useRef, useState } from "react";

import CrisisInlineCard from "@/components/Crisis/CrisisInlineCard";
import CrisisPanel from "@/components/Crisis/CrisisPanel";
import SOSButton from "@/components/Crisis/SOSButton";
import MessageFeedback from "@/components/Feedback/MessageFeedback";
import SessionFeedback from "@/components/Feedback/SessionFeedback";
import { cn } from "@/lib/cn";
import { useChat } from "@/hooks/useChat";
import { useSidebar } from "@/hooks/useSidebar";
import { useThemeTokens } from "@/hooks/useThemeTokens";

import { EmptyState } from "./EmptyState";
import InputArea from "./InputArea";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

/**
 * Главный контейнер чата.
 *
 * Шапки больше нет — её функции ушли в RightDock (тоггл темы, аватар).
 * SOS-кнопка — единственное, что выходит за пределы чата визуально:
 * она абсолютно позиционируется в правом верхнем углу через RightDock-зону,
 * но рендерится здесь, потому что зависит от crisisLevel из useChat.
 *
 * Layout:
 *   [SOS top-right]
 *   [scrollable messages area]
 *     EmptyState (если нет сообщений)
 *     или MessageBubble * N + CrisisInlineCard + MessageFeedback + TypingIndicator
 *   [SessionFeedback (когда нажали "Завершить")]
 *   [Error bar]
 *   [InputArea]
 */
export default function ChatContainer() {
  const t = useThemeTokens();
  const chat = useChat();
  const { isOpen: isSidebarOpen } = useSidebar();
  const [crisisPanelOpen, setCrisisPanelOpen] = useState(false);
  const [sessionEnded, setSessionEnded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Авто-скролл к последнему сообщению
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat.messages, chat.isTyping]);

  // Авто-открытие кризисной панели при immediate
  useEffect(() => {
    if (chat.crisisLevel === "immediate" && !crisisPanelOpen) {
      setCrisisPanelOpen(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chat.crisisLevel]);

  // Контакты из последнего ответа бота (для модалки SOS)
  const lastBotMessage = [...chat.messages]
    .reverse()
    .find((m) => m.role === "assistant");
  const contactsForPanel = lastBotMessage?.crisisContacts ?? [];

  return (
    <div className="flex flex-col h-full w-full relative overflow-hidden">
      {/* SOS — абсолютно в правом верхнем углу контентной области.
          На md+ — слева от RightDock-аватара. На мобиле — справа сверху. */}
      <div className="absolute top-3 right-3 md:top-6 md:right-[120px] lg:right-[130px] z-30">
        <SOSButton
          crisisLevel={chat.crisisLevel}
          onClick={() => setCrisisPanelOpen(true)}
        />
      </div>

      {/* Scrollable messages area */}
      <div
        className={cn(
          "flex-1 overflow-y-auto overflow-x-hidden w-full p-4 sm:p-6 lg:p-8 md:pr-[260px] lg:pr-[280px] flex flex-col custom-scrollbar transition-all duration-500",
          !isSidebarOpen && "md:pl-16 lg:pl-24",
        )}
      >
        <div className="w-full max-w-3xl mx-auto flex-1 flex flex-col">
          {chat.messages.length === 0 ? (
            <div className="flex-1 flex items-center justify-center">
              <EmptyState />
            </div>
          ) : (
            <div className="w-full flex flex-col mt-auto pt-10">
              {chat.messages.map((msg, idx) => {
                const isLast = idx === chat.messages.length - 1;
                return (
                  <div key={msg.id}>
                    <MessageBubble
                      role={msg.role}
                      content={msg.content}
                      animateTyping={msg.role === "assistant" && isLast}
                    />
                    {msg.role === "assistant" &&
                      msg.crisisLevel &&
                      msg.crisisContacts && (
                        <CrisisInlineCard
                          level={msg.crisisLevel}
                          contacts={msg.crisisContacts}
                        />
                      )}
                    {msg.role === "assistant" && (
                      <MessageFeedback
                        messageId={msg.id}
                        onFeedback={chat.sendFeedback}
                      />
                    )}
                  </div>
                );
              })}
              {chat.isTyping && <TypingIndicator />}

              {sessionEnded && (
                <SessionFeedback
                  onSubmit={async (event) => {
                    await chat.sendFeedback(event);
                  }}
                  onSkip={() => setSessionEnded(false)}
                />
              )}

              <div ref={messagesEndRef} className="h-4" />
            </div>
          )}

          {/* Кнопка "Завершить" — только если есть ответы бота и сессия не завершена */}
          {chat.messages.some((m) => m.role === "assistant") &&
            !sessionEnded &&
            chat.messages.length > 0 && (
              <button
                type="button"
                onClick={() => setSessionEnded(true)}
                className={cn(
                  "self-center text-xs px-3 py-1 rounded-full transition-colors mb-4",
                  t.textMuted,
                  t.btnHover,
                )}
              >
                Завершить и оставить отзыв
              </button>
            )}
        </div>
      </div>

      {/* Ошибка */}
      {chat.error && (
        <div
          className={cn(
            "border-t px-4 py-2 text-sm transition-all duration-500",
            "bg-crisis-100/80 border-crisis-300 text-crisis-800",
            !isSidebarOpen && "md:pl-16 lg:pl-24",
            "md:pr-[260px] lg:pr-[280px]",
          )}
        >
          <div className="max-w-3xl mx-auto">⚠️ {chat.error}</div>
        </div>
      )}

      {/* Поле ввода */}
      <div
        className={cn(
          "transition-all duration-500",
          !isSidebarOpen && "md:pl-16 lg:pl-24",
          "md:pr-[260px] lg:pr-[280px]",
        )}
      >
        <InputArea
          onSend={chat.sendMessage}
          disabled={chat.isTyping}
          placeholder={
            chat.messages.length === 0
              ? "Расскажи, что у тебя сейчас..."
              : "Напиши сообщение..."
          }
        />
      </div>

      {/* Модалка кризисных контактов */}
      <CrisisPanel
        isOpen={crisisPanelOpen}
        onClose={() => setCrisisPanelOpen(false)}
        contacts={contactsForPanel}
      />
    </div>
  );
}
