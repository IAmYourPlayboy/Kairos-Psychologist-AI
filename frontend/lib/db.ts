/**
 * Локальная БД в браузере (IndexedDB через Dexie.js).
 *
 * Зачем: оффлайн-кэш чатов. Пользователь должен иметь возможность:
 * - Закрыть вкладку и вернуться → видеть свою историю
 * - Открыть приложение без сети → видеть прошлые сообщения
 * - В будущем (Блок 15) — синхронизировать накопленные локально сообщения,
 *   когда сеть появится / когда пользователь зарегистрируется.
 *
 * SyncStatus:
 * - "local"   — существует только на устройстве (гость или офлайн)
 * - "pending" — отправлено на сервер, ждёт подтверждения (резерв на Блок 15)
 * - "synced"  — подтверждено сервером (есть message_id с бекенда)
 * - "failed"  — ошибка отправки (можно повторить)
 *
 * Это совпадает с UIMessage.status в lib/types.ts — намеренно.
 */

import Dexie, { type EntityTable } from "dexie";

import type { ChatRole, CrisisContact, CrisisLevel } from "./types";

// ============================================================================
// Типы записей в БД
// ============================================================================

export type SyncStatus = "local" | "pending" | "synced" | "failed";

/**
 * Локальная сессия чата. id совпадает с session_id на сервере.
 */
export interface LocalSession {
  id: string; // UUID, совпадает с server session_id
  guestId: string | null;
  createdAt: string; // ISO timestamp
  updatedAt: string; // ISO timestamp последнего сообщения
  messageCount: number;
  crisisLevelMax: CrisisLevel; // максимум за сессию
  syncStatus: SyncStatus;
}

/**
 * Локальное сообщение. id совпадает с server message_id если synced,
 * или сгенерирован клиентом для оптимистичных user-сообщений.
 */
export interface LocalMessage {
  id: string;
  sessionId: string;
  role: ChatRole;
  content: string;
  createdAt: string; // ISO timestamp
  // Метаданные (только для assistant)
  crisisLevel?: CrisisLevel;
  crisisContacts?: CrisisContact[];
  // Статус синхронизации
  syncStatus: SyncStatus;
}

/**
 * Операция в очереди синхронизации.
 * Используется в Блоке 15 для повторной отправки при восстановлении сети.
 */
export interface SyncOperation {
  id?: number; // auto-increment
  operation: "send_message" | "send_feedback";
  payload: unknown; // структура зависит от operation
  createdAt: string;
  attempts: number;
}

// ============================================================================
// Схема БД
// ============================================================================

class KairosDB extends Dexie {
  // Декларации таблиц с типами
  sessions!: EntityTable<LocalSession, "id">;
  messages!: EntityTable<LocalMessage, "id">;
  syncQueue!: EntityTable<SyncOperation, "id">;

  constructor() {
    super("kairos");

    // Версия 1: основные таблицы
    // Индексы: первичный ключ + поля для частых запросов
    this.version(1).stores({
      sessions: "id, guestId, createdAt, updatedAt, syncStatus",
      messages: "id, sessionId, createdAt, syncStatus",
      syncQueue: "++id, operation, createdAt",
    });
  }
}

// ============================================================================
// Singleton-экземпляр (создаётся лениво на клиенте)
// ============================================================================

let _db: KairosDB | null = null;

/**
 * Получить экземпляр БД. Инициализируется лениво при первом обращении
 * (только на клиенте — Dexie не работает в SSR).
 *
 * Возвращает null если IndexedDB недоступен (SSR / приватный режим браузера).
 */
export function getDB(): KairosDB | null {
  if (typeof window === "undefined") return null;
  if (typeof indexedDB === "undefined") return null; // приватный режим
  if (!_db) {
    _db = new KairosDB();
  }
  return _db;
}

// ============================================================================
// Высокоуровневые операции (используются из useChat)
// ============================================================================

/**
 * Сохранить сообщение в локальную БД.
 * Если БД недоступна — тихо игнорируем (не ломаем UX).
 */
export async function saveLocalMessage(msg: LocalMessage): Promise<void> {
  const db = getDB();
  if (!db) return;
  try {
    await db.messages.put(msg);
    // Обновляем сессию (счётчик + время + max crisis level)
    await touchSession(msg);
  } catch (e) {
    console.error("[Dexie] saveLocalMessage failed:", e);
  }
}

/**
 * Обновить статус сообщения (например, после успешной отправки).
 */
export async function updateMessageStatus(
  id: string,
  patch: Partial<LocalMessage>,
): Promise<void> {
  const db = getDB();
  if (!db) return;
  try {
    await db.messages.update(id, patch);
  } catch (e) {
    console.error("[Dexie] updateMessageStatus failed:", e);
  }
}

/**
 * Загрузить все сообщения сессии из локальной БД.
 * Сортировка по createdAt (asc).
 */
export async function loadSessionMessages(
  sessionId: string,
): Promise<LocalMessage[]> {
  const db = getDB();
  if (!db) return [];
  try {
    const rows = await db.messages
      .where("sessionId")
      .equals(sessionId)
      .toArray();
    rows.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
    return rows;
  } catch (e) {
    console.error("[Dexie] loadSessionMessages failed:", e);
    return [];
  }
}

/**
 * Получить список сессий (для будущей страницы истории чатов).
 * Сортировка: самые свежие сверху.
 */
export async function listSessions(
  limit = 50,
): Promise<LocalSession[]> {
  const db = getDB();
  if (!db) return [];
  try {
    const rows = await db.sessions
      .orderBy("updatedAt")
      .reverse()
      .limit(limit)
      .toArray();
    return rows;
  } catch (e) {
    console.error("[Dexie] listSessions failed:", e);
    return [];
  }
}

/**
 * Удалить сессию и все её сообщения (для кнопки «Удалить эту беседу»).
 */
export async function deleteSession(sessionId: string): Promise<void> {
  const db = getDB();
  if (!db) return;
  try {
    await db.transaction("rw", db.sessions, db.messages, async () => {
      await db.messages.where("sessionId").equals(sessionId).delete();
      await db.sessions.delete(sessionId);
    });
  } catch (e) {
    console.error("[Dexie] deleteSession failed:", e);
  }
}

/**
 * Полная очистка локальных данных (для кнопки «Удалить всё» в настройках).
 */
export async function clearAllLocalData(): Promise<void> {
  const db = getDB();
  if (!db) return;
  try {
    await db.transaction(
      "rw",
      db.sessions,
      db.messages,
      db.syncQueue,
      async () => {
        await db.sessions.clear();
        await db.messages.clear();
        await db.syncQueue.clear();
      },
    );
  } catch (e) {
    console.error("[Dexie] clearAllLocalData failed:", e);
  }
}

// ============================================================================
// Внутренние утилиты
// ============================================================================

/**
 * Обновить (или создать) запись о сессии после нового сообщения.
 * Считаем messageCount, обновляем updatedAt и crisisLevelMax.
 */
async function touchSession(msg: LocalMessage): Promise<void> {
  const db = getDB();
  if (!db) return;
  const existing = await db.sessions.get(msg.sessionId);
  const guestId = readGuestId();
  const now = msg.createdAt;

  if (!existing) {
    const session: LocalSession = {
      id: msg.sessionId,
      guestId,
      createdAt: now,
      updatedAt: now,
      messageCount: 1,
      crisisLevelMax: msg.crisisLevel ?? "normal",
      syncStatus: msg.syncStatus,
    };
    await db.sessions.put(session);
    return;
  }

  // Обновляем существующую сессию
  await db.sessions.update(msg.sessionId, {
    updatedAt: now,
    messageCount: existing.messageCount + 1,
    crisisLevelMax: maxCrisis(existing.crisisLevelMax, msg.crisisLevel),
    // syncStatus сессии = худший статус её сообщений
    syncStatus: worseSyncStatus(existing.syncStatus, msg.syncStatus),
  });
}

/**
 * Сравнение уровней кризиса (immediate > high > elevated > normal).
 */
function maxCrisis(
  a: CrisisLevel,
  b: CrisisLevel | undefined,
): CrisisLevel {
  if (!b) return a;
  const order: CrisisLevel[] = ["normal", "elevated", "high", "immediate"];
  return order.indexOf(a) >= order.indexOf(b) ? a : b;
}

/**
 * Сравнение syncStatus: failed > local > pending > synced.
 * Идея: сессия считается «не сихнхронизированной», если хоть одно сообщение
 * не дошло до сервера.
 */
function worseSyncStatus(a: SyncStatus, b: SyncStatus): SyncStatus {
  const order: SyncStatus[] = ["synced", "pending", "local", "failed"];
  return order.indexOf(a) >= order.indexOf(b) ? a : b;
}

/**
 * Безопасное чтение guest_id из localStorage (тот же ключ, что в useSession).
 */
function readGuestId(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem("kairos.guest_id");
  } catch {
    return null;
  }
}
