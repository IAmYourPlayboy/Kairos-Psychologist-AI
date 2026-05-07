/**
 * API-клиент для эндпоинтов /api/sessions/*.
 *
 * Backend истина после логина. Dexie — кэш для оффлайна и быстрой загрузки.
 *
 * Стратегия:
 * - Гость: сессии живут в Dexie + бекенде (по guest_id, через /api/chat).
 * - При логине/регистрации: backend автоматически мигрирует guest сессии
 *   (см. backend/app/api/auth.py).
 * - На новом устройстве: вызываем `pullSessionsFromServer()` один раз,
 *   чтобы наполнить Dexie из бекенда.
 */

import { request } from "./api";
import { getDB, type LocalMessage, type LocalSession } from "./db";
import type { ChatRole, CrisisLevel } from "./types";

// ============================================================================
// Типы
// ============================================================================

export interface SessionSummary {
  id: string;
  created_at: string;
  ended_at: string | null;
  message_count: number;
  crisis_level_max: "normal" | "elevated" | "high" | "immediate" | string;
  outcome: string | null;
  duration_seconds: number | null;
  title: string;
  last_message_at: string | null;
}

export interface SessionMessageItem {
  id: string;
  role: "user" | "assistant" | "system" | string;
  content: string;
  created_at: string;
  crisis_level: string | null;
}

export interface SessionDetail {
  session: SessionSummary;
  messages: SessionMessageItem[];
}

// ============================================================================
// API
// ============================================================================

export async function listSessions(): Promise<SessionSummary[]> {
  const r = await request<undefined, { sessions: SessionSummary[] }>(
    "/api/sessions",
  );
  return r.sessions;
}

export async function getSession(id: string): Promise<SessionDetail> {
  return request<undefined, SessionDetail>(`/api/sessions/${id}`);
}

export async function deleteServerSession(id: string): Promise<void> {
  await request<undefined, { ok: boolean }>(`/api/sessions/${id}`, {
    method: "DELETE",
  });
}

export async function migrateGuestToCurrentUser(
  guestId: string,
): Promise<{ ok: boolean; sessions_migrated: number; facts_migrated: number }> {
  return request<
    { guest_id: string },
    { ok: boolean; sessions_migrated: number; facts_migrated: number }
  >("/api/sessions/migrate", {
    method: "POST",
    body: { guest_id: guestId },
  });
}

// ============================================================================
// Pull в Dexie (для нового устройства)
// ============================================================================

/**
 * Подтянуть сессии текущего залогиненного пользователя в локальный Dexie.
 *
 * Сценарий: пользователь зарегистрировался на ноутбуке, потом зашёл с
 * телефона. На телефоне Dexie пуст — `useChat` не покажет историю.
 * Вызываем эту функцию один раз при логине, чтобы наполнить Dexie.
 *
 * Стратегия: upsert по id. Локальные unsync'нутые гостевые сессии не
 * затираем (они мигрируют на сервер в следующий момент через /api/chat).
 *
 * Сообщения внутри сессий подтягиваются ленивo — `getSession(id)` вызывается
 * по требованию когда пользователь открывает конкретный чат.
 */
export async function pullSessionsFromServer(): Promise<void> {
  const db = getDB();
  if (!db) return;
  let serverSessions: SessionSummary[];
  try {
    serverSessions = await listSessions();
  } catch {
    // 401 / network — тихо выходим, useChat работает с локальными
    return;
  }

  for (const s of serverSessions) {
    const local: LocalSession = {
      id: s.id,
      guestId: null,  // у залогиненного нет привязки к гостю на клиенте
      createdAt: s.created_at,
      updatedAt: s.last_message_at ?? s.created_at,
      messageCount: s.message_count,
      crisisLevelMax: (s.crisis_level_max as CrisisLevel) ?? "normal",
      syncStatus: "synced",
    };
    try {
      await db.sessions.put(local);
    } catch {
      // продолжаем
    }
  }
}

/**
 * Подтянуть сообщения конкретной сессии в Dexie.
 * Используется когда пользователь открывает старый чат.
 */
export async function pullSessionMessages(sessionId: string): Promise<void> {
  const db = getDB();
  if (!db) return;
  try {
    const detail = await getSession(sessionId);
    for (const m of detail.messages) {
      const local: LocalMessage = {
        id: m.id,
        sessionId,
        role: m.role as ChatRole,
        content: m.content,
        createdAt: m.created_at,
        crisisLevel: (m.crisis_level as CrisisLevel | undefined) ?? undefined,
        syncStatus: "synced",
      };
      await db.messages.put(local);
    }
  } catch {
    // тихо
  }
}
