"use client";

/**
 * Хук «можно ли сейчас предложить ASQ?».
 *
 * Условия (ALL):
 * 1. Сообщений >= MIN_MESSAGES (не сразу после первого).
 * 2. В последних N ассистент-сообщениях был хотя бы один с
 *    crisis_level in ["elevated", "high"]. immediate не требует ASQ —
 *    модалка кризиса уже открыта.
 * 3. Backend разрешает (frequency cap не сработал — see /should-offer).
 * 4. Пользователь ещё не пройдил/отклонил ASQ в текущем UI-состоянии.
 *
 * Этот хук — **только** про предложение. Финальная защита от спама
 * (7 дней) — на бекенде через mark-offered + should-offer.
 */

import { useEffect, useState } from "react";

import { shouldOffer } from "@/lib/screening";
import type { CrisisLevel } from "@/lib/types";

const MIN_MESSAGES_BEFORE_OFFER = 3;
const CRISIS_LOOKBACK = 5;

interface UseScreeningOfferArgs {
  identifier: string | null;
  messageCount: number;
  /** crisis_level последних bot-сообщений (новейший в конце). */
  recentBotCrisisLevels: CrisisLevel[];
  /** Не предлагать в этой сессии (уже прошёл/отклонил). */
  dismissedInSession: boolean;
}

export function useShouldOfferASQ({
  identifier,
  messageCount,
  recentBotCrisisLevels,
  dismissedInSession,
}: UseScreeningOfferArgs): boolean {
  const [serverAllows, setServerAllows] = useState<boolean | null>(null);

  // Frontend pre-check: имеет смысл вообще спрашивать backend?
  const frontendQualifies =
    !dismissedInSession
    && messageCount >= MIN_MESSAGES_BEFORE_OFFER
    && recentBotCrisisLevels
      .slice(-CRISIS_LOOKBACK)
      .some((l) => l === "elevated" || l === "high");

  // Запрос к backend (frequency cap) только когда frontend уже квалифицировался,
  // чтобы не дёргать сервер на каждое сообщение.
  useEffect(() => {
    if (!frontendQualifies || !identifier) {
      setServerAllows(null);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const allowed = await shouldOffer(identifier, "asq");
        if (!cancelled) setServerAllows(allowed);
      } catch {
        // Если бекенд упал — не предлагаем (молчим, не ломаем UX)
        if (!cancelled) setServerAllows(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // identifier и frontendQualifies — главные триггеры. recentBotCrisisLevels
    // меняется на каждое сообщение, но frontendQualifies абсорбирует это.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [identifier, frontendQualifies]);

  return frontendQualifies && serverAllows === true;
}
