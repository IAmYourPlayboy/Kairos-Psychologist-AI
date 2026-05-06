"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import CrisisInlineCard from "@/components/Crisis/CrisisInlineCard";
import CrisisPanel from "@/components/Crisis/CrisisPanel";
import SOSButton from "@/components/Crisis/SOSButton";
import MessageFeedback from "@/components/Feedback/MessageFeedback";
import SessionFeedback from "@/components/Feedback/SessionFeedback";
import { useChat } from "@/hooks/useChat";

import InputArea from "./InputArea";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

/**
 * Главный контейнер чата.
 *
 * Структура:
 * ┌─────────────────────────────────────┐
 * │ Шапка: Название + SOS-кнопка         │
 * ├─────────────────────────────────────┤
 * │                                       │
 * │  Сообщения (авто-скролл вниз)        │
 * │                                       │
 * │  [Карточка кризисных контактов]      │
 * │                                       │
 * │                       [Печатает...]   │
 * ├─────────────────────────────────────┤
 * │ [Ошибка, если есть]                  │
 * │ [Поле ввода]                         │
 * │ Дисклеймер про специалистов           │
 * └─────────────────────────────────────┘
 */
export default function ChatContainer() {
  const chat = useChat();
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

  // Контакты из последнего ответа бота (для панели)
  const lastBotMessage = [...chat.messages]
    .reverse()
    .find((m) => m.role === "assistant");
  const contactsForPanel = lastBotMessage?.crisisContacts ?? [];

  return (
    <div className="flex flex-col h-screen bg-warm-50">
      {/* Шапка */}
      <header className="border-b border-warm-200 bg-warm-50/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-warm-900">Кайрос</h1>
            <p className="text-xs text-warm-600">Первая психологическая помощь</p>
          </div>
          <div className="flex items-center gap-2">
            {/* Ссылка на досье (Сессия 18+) */}
            <Link
              href="/profile"
              className="text-xs text-warm-600 hover:text-warm-900 transition-colors px-2 py-1 rounded hover:bg-warm-100"
              aria-label="Что Кайрос помнит обо мне"
            >
              Профиль
            </Link>
            {/* Кнопка «Завершить сессию» — открывает финальную карточку feedback.
                Показывается только если есть хотя бы один ответ бота, и пока
                ещё не открыта карточка feedback. */}
            {chat.messages.some((m) => m.role === "assistant") &&
              !sessionEnded && (
                <button
                  type="button"
                  onClick={() => setSessionEnded(true)}
                  className="text-xs text-warm-600 hover:text-warm-900 transition-colors px-2 py-1 rounded hover:bg-warm-100"
                  aria-label="Завершить сессию и оставить отзыв"
                >
                  Завершить
                </button>
              )}
            <SOSButton
              crisisLevel={chat.crisisLevel}
              onClick={() => setCrisisPanelOpen(true)}
            />
          </div>
        </div>
      </header>

      {/* Лента сообщений */}
      <main className="flex-1 overflow-y-auto px-4 py-4">
        <div className="max-w-3xl mx-auto">
          {chat.messages.length === 0 ? (
            <EmptyState />
          ) : (
            <>
              {chat.messages.map((msg) => (
                <div key={msg.id} className="animate-fade-in">
                  <MessageBubble role={msg.role} content={msg.content} />
                  {/* Кризисная карточка под ответом бота */}
                  {msg.role === "assistant" &&
                    msg.crisisLevel &&
                    msg.crisisContacts && (
                      <CrisisInlineCard
                        level={msg.crisisLevel}
                        contacts={msg.crisisContacts}
                      />
                    )}
                  {/* Кнопки thumbs up/down под каждым ответом бота
                      (data flywheel — главный сигнал качества) */}
                  {msg.role === "assistant" && (
                    <MessageFeedback
                      messageId={msg.id}
                      onFeedback={chat.sendFeedback}
                    />
                  )}
                </div>
              ))}
              {chat.isTyping && <TypingIndicator />}

              {/* Финальная карточка обратной связи по сессии */}
              {sessionEnded && (
                <SessionFeedback
                  onSubmit={async (event) => {
                    await chat.sendFeedback(event);
                  }}
                  onSkip={() => setSessionEnded(false)}
                />
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </main>

      {/* Ошибка */}
      {chat.error && (
        <div className="bg-crisis-100 border-t border-crisis-300 px-4 py-2 text-sm text-crisis-800">
          <div className="max-w-3xl mx-auto flex items-center justify-between">
            <span>⚠️ {chat.error}</span>
          </div>
        </div>
      )}

      {/* Поле ввода */}
      <InputArea
        onSend={chat.sendMessage}
        disabled={chat.isTyping}
        placeholder={
          chat.messages.length === 0
            ? "Расскажи, что у тебя сейчас..."
            : "Напиши сообщение..."
        }
      />

      {/* Модалка кризисных контактов */}
      <CrisisPanel
        isOpen={crisisPanelOpen}
        onClose={() => setCrisisPanelOpen(false)}
        contacts={contactsForPanel}
      />
    </div>
  );
}

/**
 * Пустое состояние — приветствие при первом заходе.
 */
function EmptyState() {
  return (
    <div className="text-center py-12 max-w-md mx-auto">
      <h2 className="text-xl font-semibold text-warm-900 mb-3">
        Здесь можно говорить как есть
      </h2>
      <p className="text-warm-700 leading-relaxed mb-6">
        Я — Кайрос. Не психолог и не врач, но я рядом, если тебе тяжело.
        Расскажи что происходит — я постараюсь помочь.
      </p>
      <p className="text-sm text-warm-500">
        Если сейчас критическая ситуация — нажми{" "}
        <span className="font-semibold">SOS</span> в правом верхнем углу.
      </p>
    </div>
  );
}
