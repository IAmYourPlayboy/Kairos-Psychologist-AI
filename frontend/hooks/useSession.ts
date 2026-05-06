"use client";

import { useCallback, useEffect, useState } from "react";

/**
 * Хук управления session_id и guest_id для гостевого пользователя.
 *
 * - guest_id хранится в localStorage навсегда.
 * - session_id хранится в localStorage (поменяли с sessionStorage в Phase 3),
 *   потому что теперь у нас мульти-сессии: пользователь может иметь несколько
 *   бесед и переключаться между ними. Активная сессия — та, что в localStorage.
 */

const GUEST_ID_KEY = "kairos.guest_id";
const SESSION_ID_KEY = "kairos.session_id";

function generateUuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function useSession() {
  const [guestId, setGuestId] = useState<string | null>(null);
  const [sessionId, setSessionIdState] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    let gid = localStorage.getItem(GUEST_ID_KEY);
    if (!gid) {
      gid = generateUuid();
      localStorage.setItem(GUEST_ID_KEY, gid);
    }
    setGuestId(gid);

    let sid = localStorage.getItem(SESSION_ID_KEY);
    if (!sid) {
      sid = generateUuid();
      localStorage.setItem(SESSION_ID_KEY, sid);
    }
    setSessionIdState(sid);
  }, []);

  const resetSession = useCallback(() => {
    if (typeof window === "undefined") return;
    const newSid = generateUuid();
    localStorage.setItem(SESSION_ID_KEY, newSid);
    setSessionIdState(newSid);
  }, []);

  const switchToSession = useCallback((id: string) => {
    if (typeof window === "undefined") return;
    localStorage.setItem(SESSION_ID_KEY, id);
    setSessionIdState(id);
  }, []);

  return { guestId, sessionId, resetSession, switchToSession };
}
