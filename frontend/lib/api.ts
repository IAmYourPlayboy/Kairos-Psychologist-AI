/**
 * API-обёртка для общения с бекендом Кайроса.
 *
 * Все запросы идут на относительный путь /api/...
 * Next.js rewrites (см. next.config.js) проксируют их на FastAPI (порт 8001).
 *
 * Особенности:
 * - credentials: "include" — пробрасываем cookies (для будущей JWT-аутентификации)
 * - таймаут 30 секунд (LLM может думать)
 * - JSON-only API
 */

import type {
  ApiError,
  ChatRequest,
  ChatResponse,
  FeedbackRequest,
  FeedbackResponse,
} from "./types";

const DEFAULT_TIMEOUT_MS = 30_000;

/**
 * Базовая ошибка API. Содержит структурированную информацию.
 */
export class ApiClientError extends Error {
  readonly status: number;
  readonly type: string;
  readonly requestId: string | null;
  readonly details: unknown;

  constructor(payload: ApiError["error"]) {
    super(payload.message);
    this.name = "ApiClientError";
    this.status = payload.status;
    this.type = payload.type;
    this.requestId = payload.request_id ?? null;
    this.details = payload.details ?? null;
  }
}

/**
 * Общий fetch-хелпер с обработкой ошибок и таймаутом.
 */
async function request<TBody, TResponse>(
  path: string,
  options: {
    method?: "GET" | "POST";
    body?: TBody;
    timeoutMs?: number;
    signal?: AbortSignal;
  } = {},
): Promise<TResponse> {
  const { method = "GET", body, timeoutMs = DEFAULT_TIMEOUT_MS, signal } = options;

  // Объединяем внешний signal (если есть) с нашим таймаутом
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  // Если внешний signal отменился — отменяем и наш
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener("abort", () => controller.abort());
  }

  try {
    const response = await fetch(path, {
      method,
      credentials: "include",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    // Парсим ответ
    let data: unknown;
    try {
      data = await response.json();
    } catch {
      // Не JSON — необычная ошибка
      throw new ApiClientError({
        type: "non_json_response",
        status: response.status,
        message: `Сервер вернул не-JSON (${response.status})`,
      });
    }

    if (!response.ok) {
      // Бекенд возвращает ошибку в формате { error: { type, status, message, ... } }
      const apiError = (data as ApiError).error;
      if (apiError) {
        throw new ApiClientError(apiError);
      }
      // Иначе — просто текст ошибки
      throw new ApiClientError({
        type: "unknown",
        status: response.status,
        message: `HTTP ${response.status}`,
      });
    }

    return data as TResponse;
  } catch (e) {
    // AbortError = таймаут или отмена пользователем
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new ApiClientError({
        type: "timeout",
        status: 0,
        message: "Время ожидания ответа истекло. Попробуй ещё раз.",
      });
    }
    // ApiClientError пробрасываем как есть
    if (e instanceof ApiClientError) throw e;
    // Сеть недоступна
    throw new ApiClientError({
      type: "network",
      status: 0,
      message: "Нет связи с сервером. Проверь интернет.",
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

// ============================================================================
// Эндпоинты
// ============================================================================

/**
 * GET /api/health — проверка что бекенд жив.
 */
export async function getHealth(): Promise<{
  status: string;
  app: string;
  version: string;
}> {
  return request("/api/health");
}

/**
 * POST /api/chat — отправить сообщение боту, получить ответ.
 */
export async function postChat(
  body: ChatRequest,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  return request<ChatRequest, ChatResponse>("/api/chat", {
    method: "POST",
    body,
    signal,
  });
}

/**
 * POST /api/feedback — отправить событие обратной связи.
 */
export async function postFeedback(
  body: FeedbackRequest,
): Promise<FeedbackResponse> {
  return request<FeedbackRequest, FeedbackResponse>("/api/feedback", {
    method: "POST",
    body,
  });
}
