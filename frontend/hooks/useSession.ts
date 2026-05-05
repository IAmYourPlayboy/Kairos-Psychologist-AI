"use client";

import { useEffect, useState } from "react";

/**
 * Хук управления session_id и guest_id для гостевого пользователя.
 *
 * Логика:
 * - guest_id создаётся при первом визите и хранится в localStorage навсегда
 *   (до регистрации, потом он привяжется к user_id через /api/sync/migrate).
 * - session_id создаётся при первом сообщении в каждой новой беседе.
 *   После закрытия вкладки и возврата — можно либо продолжить старую сессию,
 *   либо начать новую (это решение принимает useChat / страница).
 *
 * Решение MVP: session_id живёт в sessionStorage (умирает при закрытии вкладки),
 * guest_id — в localStorage (постоянный).
 */

const GUEST_ID_KEY = "kairos.guest_id";
const SESSION_ID_KEY = "kairos.session_id";

function generateUuid(): string {
  // crypto.randomUUID() доступен в браузерах с 2022+ (https://caniuse.com/mdn-api_crypto_randomuuid)
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  // Fallback (на случай старого браузера)
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function useSession() {
  const [guestId, setGuestId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Инициализация при первом рендере (на клиенте)
  useEffect(() => {
    if (typeof window === "undefined") return;

    // Гостевой ID — постоянный
    let gid = localStorage.getItem(GUEST_ID_KEY);
    if (!gid) {
      gid = generateUuid();
      localStorage.setItem(GUEST_ID_KEY, gid);
    }
    setGuestId(gid);

    // Сессия — на одну вкладку
    let sid = sessionStorage.getItem(SESSION_ID_KEY);
    if (!sid) {
      sid = generateUuid();
      sessionStorage.setItem(SESSION_ID_KEY, sid);
    }
    setSessionId(sid);
  }, []);

  /**
   * Начать новую беседу: создать новый session_id (не трогая guest_id).
   */
  function resetSession() {
    if (typeof window === "undefined") return;
    const newSid = generateUuid();
    sessionStorage.setItem(SESSION_ID_KEY, newSid);
    setSessionId(newSid);
  }

  return { guestId, sessionId, resetSession };
}
