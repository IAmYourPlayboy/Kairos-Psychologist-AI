"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiClientError, postChat, postFeedback } from "@/lib/api";
import {
  loadSessionMessages,
  saveLocalMessage,
  updateMessageStatus,
  type LocalMessage,
} from "@/lib/db";
import type {
  ChatMessageHistory,
  CrisisLevel,
  FeedbackEventType,
  UIMessage,
} from "@/lib/types";
import { useSession } from "./useSession";

/**
 * Главный хук чата.
 *
 * Управляет:
 * - Списком сообщений (UI)
 * - Отправкой сообщения и получением ответа от /api/chat
 * - Текущим состоянием (печатает / ошибка)
 * - Кризисным уровнем (для UI индикаторов: SOS-кнопка, карточки контактов)
 * - Отправкой feedback-событий
 *
 * История на сервер шлётся в формате [{role, content}, ...] (без UUID).
 * Сервер сам сохраняет всё в БД для data flywheel.
 */

interface UseChatOptions {
  ageGroup?: "child" | "youth" | "adult";
}

function generateUuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2);
}

function nowIso(): string {
  return new Date().toISOString();
}

export function useChat(options: UseChatOptions = {}) {
  const { ageGroup = "adult" } = options;
  const { guestId, sessionId, resetSession } = useSession();

  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [crisisLevel, setCrisisLevel] = useState<CrisisLevel>("normal");

  // AbortController для отмены текущего запроса
  const abortRef = useRef<AbortController | null>(null);

  // Set ID-шников сообщений созданных в ТЕКУЩЕМ маунте.
  // Сообщения загруженные из Dexie сюда НЕ попадают.
  // Используется в UI чтобы анимировать печать (HumanTypingEffect)
  // только для свежих ответов бота — а не повторно при ре-маунте
  // ChatContainer (например, после возврата с /settings).
  const freshMessageIdsRef = useRef<Set<string>>(new Set());

  /**
   * При смене sessionId — полностью пересинхронизируем UI-state с новой сессией.
   *
   * Семантика: useChat представляет данные ИМЕННО ДЛЯ текущего sessionId.
   * Когда sessionId меняется (новая беседа / переключение на старую):
   *   1. Отменяем in-flight запрос предыдущей сессии (иначе ответ придёт
   *      в новую сессию и испортит её state).
   *   2. Сбрасываем messages/crisisLevel/error/isTyping — мы больше не
   *      смотрим на ту сессию.
   *   3. Загружаем историю новой сессии из Dexie. Если её нет (новая беседа) —
   *      остаёмся с пустым state, и UI покажет EmptyState.
   *
   * До этого фикса при пустой новой сессии state не сбрасывался, и
   * пользователь видел старый чат как будто кнопка «Новый разговор» не
   * сработала.
   */
  useEffect(() => {
    // 1. Отменяем in-flight запрос предыдущей сессии.
    abortRef.current?.abort();
    abortRef.current = null;

    // 2. Сбрасываем session-scoped state.
    setMessages([]);
    setCrisisLevel("normal");
    setError(null);
    setIsTyping(false);

    // 2.5. Очищаем "свежие" id'шники — при смене сессии или ре-маунте
    // ничего ещё не было «только что отправлено» в этой инстанции.
    freshMessageIdsRef.current = new Set();

    // 3. Если sessionId ещё не подгружен (первый рендер до Context init) —
    // просто остаёмся в reset-состоянии. Когда sessionId появится, эффект
    // запустится снова.
    if (!sessionId) return;

    // 4. Загружаем историю новой сессии.
    let cancelled = false;
    void (async () => {
      const local = await loadSessionMessages(sessionId);
      if (cancelled) return;
      if (local.length === 0) return; // новая беседа — state уже пустой
      const ui: UIMessage[] = local.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        createdAt: m.createdAt,
        crisisLevel: m.crisisLevel,
        crisisContacts: m.crisisContacts,
        status: m.syncStatus,
      }));
      setMessages(ui);
      // Восстанавливаем последний кризисный уровень для UI индикаторов
      const lastBot = [...local].reverse().find((m) => m.role === "assistant");
      if (lastBot?.crisisLevel) setCrisisLevel(lastBot.crisisLevel);
    })();
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  /**
   * Отправить сообщение пользователя боту.
   */
  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isTyping) return;

      setError(null);

      // 1. Добавляем пользовательское сообщение в UI сразу (оптимистично)
      const userMessage: UIMessage = {
        id: generateUuid(),
        role: "user",
        content: trimmed,
        createdAt: nowIso(),
        status: "pending",
      };
      setMessages((prev) => [...prev, userMessage]);
      freshMessageIdsRef.current.add(userMessage.id);
      freshMessageIdsRef.current.add(userMessage.id);

      // 1.5. Сразу сохраняем в локальную БД (Dexie) — на случай потери сети.
      if (sessionId) {
        const localUser: LocalMessage = {
          id: userMessage.id,
          sessionId,
          role: "user",
          content: trimmed,
          createdAt: userMessage.createdAt,
          syncStatus: "pending",
        };
        void saveLocalMessage(localUser);
      }

      // 2. Готовим историю для отправки на сервер (без только что добавленного user-сообщения).
      // Backend валидирует max_length=50 (app/api/schemas.py::ChatRequest.history).
      // Временный фикс: обрезаем до последних 50 сообщений. Системное решение —
      // вынести историю на сервер (читать из messages), планируется в Фазе 1.5 (UserState).
      const HISTORY_LIMIT = 50;
      const history: ChatMessageHistory[] = messages.slice(-HISTORY_LIMIT).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      // 3. Отправляем
      setIsTyping(true);
      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const response = await postChat(
          {
            message: trimmed,
            session_id: sessionId,
            guest_id: guestId,
            age_group: ageGroup,
            history,
          },
          controller.signal,
        );

        // 4. Помечаем user-сообщение как synced
        setMessages((prev) =>
          prev.map((m) =>
            m.id === userMessage.id ? { ...m, status: "synced" } : m,
          ),
        );
        void updateMessageStatus(userMessage.id, { syncStatus: "synced" });

        // 5. Добавляем ответ бота
        const botMessage: UIMessage = {
          id: response.message_id,
          role: "assistant",
          content: response.reply,
          createdAt: nowIso(),
          crisisLevel: response.crisis_level,
          crisisContacts: response.crisis_contacts,
          status: "synced",
        };
        setMessages((prev) => [...prev, botMessage]);
        freshMessageIdsRef.current.add(botMessage.id);
        setCrisisLevel(response.crisis_level);

        // 5.5. Сохраняем ответ бота в локальную БД (Dexie).
        // Используем session_id из ответа сервера (он канонический).
        const localBot: LocalMessage = {
          id: response.message_id,
          sessionId: response.session_id,
          role: "assistant",
          content: response.reply,
          createdAt: botMessage.createdAt,
          crisisLevel: response.crisis_level,
          crisisContacts: response.crisis_contacts,
          syncStatus: "synced",
        };
        void saveLocalMessage(localBot);

        // Если бекенд прислал llm_error — это значит был fallback.
        // В debug-режиме показываем диагностику (для разработчика).
        if (response.llm_error) {
          setError(`LLM fallback: ${response.llm_error}`);
        }
      } catch (e) {
        // Ошибка — помечаем user-сообщение как failed и показываем ошибку
        setMessages((prev) =>
          prev.map((m) =>
            m.id === userMessage.id ? { ...m, status: "failed" } : m,
          ),
        );
        void updateMessageStatus(userMessage.id, { syncStatus: "failed" });

        const errorMsg =
          e instanceof ApiClientError
            ? e.message
            : "Что-то пошло не так. Попробуй ещё раз.";
        setError(errorMsg);
      } finally {
        setIsTyping(false);
        abortRef.current = null;
      }
    },
    [messages, isTyping, sessionId, guestId, ageGroup],
  );

  /**
   * Отменить текущий запрос (если бот ещё думает).
   */
  const cancelTyping = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsTyping(false);
  }, []);

  /**
   * Очистить чат и начать новую сессию.
   */
  const resetChat = useCallback(() => {
    cancelTyping();
    setMessages([]);
    setError(null);
    setCrisisLevel("normal");
    resetSession();
  }, [cancelTyping, resetSession]);

  /**
   * Отправить feedback-событие (явное от пользователя).
   */
  const sendFeedback = useCallback(
    async (event: FeedbackEventType, messageId?: string) => {
      if (!sessionId) return;
      try {
        await postFeedback({
          session_id: sessionId,
          message_id: messageId ?? null,
          event_type: event,
        });
      } catch (e) {
        // Тихо логируем — не показываем пользователю
        // (feedback не критичен для основного потока)
        console.error("Feedback failed:", e);
      }
    },
    [sessionId],
  );

  /**
   * Свежее ли сообщение (созданное в текущем mount'е) или загружено из истории.
   * Используется UI для решения анимировать ли HumanTypingEffect — мы не
   * хотим, чтобы при возврате на /chat бот «печатал» свои старые ответы.
   */
  const isFreshMessage = useCallback(
    (id: string): boolean => freshMessageIdsRef.current.has(id),
    [],
  );

  return {
    // Состояние
    messages,
    isTyping,
    error,
    crisisLevel,
    sessionId,
    guestId,
    // Действия
    sendMessage,
    cancelTyping,
    resetChat,
    sendFeedback,
    // Утилиты
    isFreshMessage,
  };
}
