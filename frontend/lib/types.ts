/**
 * TypeScript-типы для общения с FastAPI бекендом.
 *
 * Должны соответствовать Pydantic-схемам в backend/app/api/schemas.py.
 * Если меняешь там — меняй и здесь.
 */

// ============================================================================
// Чат
// ============================================================================

export type ChatRole = "user" | "assistant";

export interface ChatMessageHistory {
  role: ChatRole;
  content: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string | null;
  guest_id?: string | null;
  age_group?: "child" | "youth" | "adult" | null;
  history?: ChatMessageHistory[];
}

export type CrisisLevel = "normal" | "elevated" | "high" | "immediate";

export type Branch = "A" | "B";

export interface CrisisContact {
  name: string;
  phone: string;
  description: string;
}

export interface ChatResponse {
  reply: string;
  session_id: string;
  message_id: string;
  crisis_level: CrisisLevel;
  crisis_contacts: CrisisContact[];
  branch: Branch | null;
  response_time_ms?: number | null;
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
  /**
   * Диагностический текст ошибки LLM (только в debug-режиме бекенда).
   * Если не null — значит реальный вызов LLM упал и был использован fallback.
   */
  llm_error?: string | null;
}

// ============================================================================
// Feedback
// ============================================================================

export type FeedbackEventType =
  | "felt_better"
  | "no_change"
  | "felt_worse"
  | "thumbs_up"
  | "thumbs_down"
  | "crisis_escalated"
  | "session_timeout"
  | "user_left";

export interface FeedbackRequest {
  session_id: string;
  message_id?: string | null;
  event_type: FeedbackEventType;
}

export interface FeedbackResponse {
  ok: boolean;
  feedback_id: string;
}

// ============================================================================
// UI-типы (только для фронта)
// ============================================================================

/**
 * Сообщение в UI чата. Объединяет user/assistant + статус.
 */
export interface UIMessage {
  id: string; // UUID, сгенерированный на клиенте
  role: ChatRole;
  content: string;
  createdAt: string; // ISO
  // Для assistant-сообщений
  crisisLevel?: CrisisLevel;
  crisisContacts?: CrisisContact[];
  // Статус отправки на сервер (для будущей оффлайн-логики, Блок 10)
  status?: "local" | "pending" | "synced" | "failed";
}

// ============================================================================
// API ошибки
// ============================================================================

/**
 * Стандартная форма ошибки от бекенда (см. middleware/error_handler.py).
 */
export interface ApiError {
  error: {
    type: string;
    status: number;
    message: string;
    request_id?: string | null;
    details?: unknown;
  };
}

// ============================================================================
// Досье (Слой восприятия — Сессия 18+)
// ============================================================================

export interface DossierQuote {
  text: string;
  created_at: string;
}

export interface DossierFact {
  id: string;
  folder: string;
  subfolder: string | null;
  summary: string;
  tags: string[];
  severity: number;
  confidence: number;
  times_mentioned: number;
  first_mentioned: string;
  last_mentioned: string;
  superseded: boolean;
  quotes: DossierQuote[];
}

export interface DossierResponse {
  facts: DossierFact[];
}

export interface DossierDeleteResponse {
  ok: boolean;
  deleted_count: number;
}
