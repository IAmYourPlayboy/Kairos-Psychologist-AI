/**
 * API-клиент для эндпоинтов /api/screening/*.
 *
 * Backend: см. backend/app/api/screening.py.
 *
 * Контракт ADR-1 (см. CLAUDE.md): ASQ-positive результат на 7 дней
 * принудительно ставит risk_level=immediate в /api/chat. На frontend
 * это значит: после прохождения positive ASQ пользователь увидит
 * crisis-панель в следующих сообщениях.
 */

import { ApiClientError, request } from "./api";

export { ApiClientError };

// ============================================================================
// Типы
// ============================================================================

export type ASQAnswer = "yes" | "no" | "decline";
export type ASQInterpretation =
  | "negative"
  | "non_acute_positive"
  | "acute_positive";

export interface ASQQuestion {
  id: number;
  text: string;
  is_acuity: boolean;
}

export interface ASQQuestionnaire {
  questionnaire: "asq";
  questions: ASQQuestion[];
  answer_options: ASQAnswer[];
}

export interface ASQResult {
  interpretation: ASQInterpretation;
  score: number;
  is_positive: boolean;
  record_id: string;
}

export type PSS4Interpretation = "low" | "moderate" | "high";

export interface PSS4Question {
  id: number;
  text: string;
  reverse: boolean;
}

export interface PSS4Questionnaire {
  questionnaire: "pss4";
  questions: PSS4Question[];
  /** Подсказки шкалы для UI (0..4 → текст). reverse применяется на бекенде. */
  scale: Record<number, string>;
}

export interface PSS4Result {
  interpretation: PSS4Interpretation;
  score: number;
  record_id: string;
}

export type QuestionnaireType = "asq" | "pss4" | "osr";

// ============================================================================
// Структуры опросников
// ============================================================================

export async function getASQQuestionnaire(): Promise<ASQQuestionnaire> {
  return request<undefined, ASQQuestionnaire>("/api/screening/asq");
}

export async function getPSS4Questionnaire(): Promise<PSS4Questionnaire> {
  return request<undefined, PSS4Questionnaire>("/api/screening/pss4");
}

// ============================================================================
// Отправка ответов
// ============================================================================

export async function submitASQ(
  sessionId: string,
  answers: Record<number, ASQAnswer>,
): Promise<ASQResult> {
  // Backend ждёт ключи как строки (JSON object keys всегда строки).
  const stringAnswers: Record<string, ASQAnswer> = {};
  for (const [k, v] of Object.entries(answers)) {
    stringAnswers[String(k)] = v;
  }
  return request<
    { session_id: string; answers: Record<string, ASQAnswer> },
    ASQResult
  >("/api/screening/asq", {
    method: "POST",
    body: { session_id: sessionId, answers: stringAnswers },
  });
}

export async function submitPSS4(
  sessionId: string,
  answers: Record<number, number>,
): Promise<PSS4Result> {
  const stringAnswers: Record<string, number> = {};
  for (const [k, v] of Object.entries(answers)) {
    stringAnswers[String(k)] = v;
  }
  return request<
    { session_id: string; answers: Record<string, number> },
    PSS4Result
  >("/api/screening/pss4", {
    method: "POST",
    body: { session_id: sessionId, answers: stringAnswers },
  });
}

// ============================================================================
// Frequency cap
// ============================================================================

/** Можно ли сейчас показать опросник этому пользователю/гостю? */
export async function shouldOffer(
  identifier: string,
  questionnaire: QuestionnaireType,
): Promise<boolean> {
  const params = new URLSearchParams({ identifier, questionnaire });
  const r = await request<undefined, { should_offer: boolean }>(
    `/api/screening/should-offer?${params}`,
  );
  return r.should_offer;
}

/** Сообщить backend'у что опросник был показан (запускает 7-дневный TTL). */
export async function markOffered(
  identifier: string,
  questionnaire: QuestionnaireType,
): Promise<void> {
  await request<
    { identifier: string; questionnaire: QuestionnaireType },
    { ok: boolean }
  >("/api/screening/mark-offered", {
    method: "POST",
    body: { identifier, questionnaire },
  });
}
