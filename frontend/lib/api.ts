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
    // Defensive coercion: по контракту error_handler.py::message всегда строка,
    // но если бэкенд внезапно вернул объект (старая версия, другой формат) —
    // не показываем пользователю "[object Object]" (JS toString).
    // Стараемся вытащить осмысленное сообщение, иначе — дефолтная строка.
    // Принимаем как unknown несмотря на тип `string` в контракте — в runtime
    // это может быть что угодно (JSON с сервера типизацию не соблюдает).
    const rawMessage = payload.message as unknown;
    let safeMessage: string;
    if (typeof rawMessage === "string") {
      safeMessage = rawMessage;
    } else if (rawMessage && typeof rawMessage === "object") {
      const obj = rawMessage as { message?: unknown; code?: unknown };
      safeMessage =
        typeof obj.message === "string"
          ? obj.message
          : typeof obj.code === "string"
          ? obj.code
          : "Непредвиденная ошибка сервера";
    } else {
      safeMessage = "Непредвиденная ошибка сервера";
    }
    super(safeMessage);
    this.name = "ApiClientError";
    this.status = payload.status;
    this.type = payload.type;
    this.requestId = payload.request_id ?? null;
    this.details = payload.details ?? null;
  }
}

// ============================================================================
// Auto-refresh: на 401 пытаемся обновить access через /api/auth/refresh.
//
// Защита от race: если параллельно идут N запросов и все получили 401,
// мы не делаем N refresh. Первый кладёт promise в `refreshInFlight`, остальные
// его await'ят. После завершения promise очищается.
//
// Защита от рекурсии: запросы на сам `/api/auth/refresh` помечаются флагом
// `skipAutoRefresh` и не триггерят повторный refresh даже на 401.
// ============================================================================

let refreshInFlight: Promise<boolean> | null = null;

async function attemptRefresh(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    try {
      const response = await fetch("/api/auth/refresh", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      return response.ok;
    } catch {
      return false;
    } finally {
      // Сбрасываем чуть позже, чтобы параллельные запросы поделили один Promise
      setTimeout(() => {
        refreshInFlight = null;
      }, 0);
    }
  })();

  return refreshInFlight;
}

/**
 * Общий fetch-хелпер с обработкой ошибок и таймаутом.
 */
async function request<TBody, TResponse>(
  path: string,
  options: {
    method?: "GET" | "POST" | "DELETE" | "PATCH";
    body?: TBody;
    timeoutMs?: number;
    signal?: AbortSignal;
    /** Не пытаться auto-refresh на 401 (для самого /api/auth/refresh). */
    skipAutoRefresh?: boolean;
  } = {},
): Promise<TResponse> {
  const {
    method = "GET",
    body,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    signal,
    skipAutoRefresh = false,
  } = options;

  // Объединяем внешний signal (если есть) с нашим таймаутом
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  // Если внешний signal отменился — отменяем и наш
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener("abort", () => controller.abort());
  }

  const doFetch = async () =>
    fetch(path, {
      method,
      credentials: "include",
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

  try {
    let response = await doFetch();

    // Auto-refresh на 401
    if (response.status === 401 && !skipAutoRefresh) {
      const refreshed = await attemptRefresh();
      if (refreshed) {
        // Повторяем оригинальный запрос с новым access cookie
        response = await doFetch();
      }
      // Если не удалось обновить — оставляем оригинальный 401, пусть caller
      // решает (показать форму логина и т.д.).
    }

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
      // FastAPI возвращает {"detail": "..."} для HTTPException — учтём
      const detail = (data as { detail?: string }).detail;
      throw new ApiClientError({
        type: "unknown",
        status: response.status,
        message: detail ?? `HTTP ${response.status}`,
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

/** Экспортируем для использования из специфичных модулей (lib/auth.ts). */
export { request };

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
