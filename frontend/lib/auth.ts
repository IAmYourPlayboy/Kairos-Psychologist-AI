/**
 * API-клиент для эндпоинтов /api/auth/*.
 *
 * Все методы используют общий ``request()`` из api.ts (с auto-refresh).
 * Сам refresh — единственный, кто отключает auto-refresh, чтобы не зациклить.
 */

import { request, ApiClientError } from "./api";

// ============================================================================
// Типы
// ============================================================================

export interface User {
  id: string;
  email: string | null;
  display_name: string | null;
  subscription_tier: "free" | "support" | "twin" | string;
  is_verified: boolean;
  created_at: string;
  /** ISO 8601. Если задан — аккаунт помечен на удаление через 7 дней. */
  deletion_scheduled_at: string | null;
}

export type ConsentType =
  | "terms_of_service"
  | "data_processing"
  | "research_anonymized";

export interface ConsentItem {
  consent_type: ConsentType;
  document_version?: string;
}

export interface AuthResponse {
  ok: boolean;
  user: User;
}

export interface ConsentStatus {
  consent_type: ConsentType;
  document_version: string;
  accepted_at: string;
  revoked_at: string | null;
}

export interface ConsentStatusResponse {
  consents: ConsentStatus[];
  has_all_required: boolean;
}

// ============================================================================
// API
// ============================================================================

/** GET /api/auth/me. Возвращает User если залогинен, кидает 401 иначе. */
export async function getMe(): Promise<User> {
  return request<undefined, User>("/api/auth/me");
}

/** POST /api/auth/login. */
export async function login(
  email: string,
  password: string,
): Promise<AuthResponse> {
  return request<{ email: string; password: string }, AuthResponse>(
    "/api/auth/login",
    { method: "POST", body: { email, password } },
  );
}

/** POST /api/auth/register. */
export async function register(input: {
  email: string;
  password: string;
  displayName?: string;
  guestId?: string | null;
  consents?: ConsentItem[];
}): Promise<AuthResponse> {
  return request<
    {
      email: string;
      password: string;
      display_name?: string;
      guest_id?: string | null;
      consents: ConsentItem[];
    },
    AuthResponse
  >("/api/auth/register", {
    method: "POST",
    body: {
      email: input.email,
      password: input.password,
      display_name: input.displayName,
      guest_id: input.guestId,
      consents: input.consents ?? [],
    },
  });
}

/** POST /api/auth/logout. */
export async function logout(everywhere = false): Promise<{ ok: boolean }> {
  return request<{ everywhere: boolean }, { ok: boolean }>("/api/auth/logout", {
    method: "POST",
    body: { everywhere },
  });
}

/** DELETE /api/auth/me — удалить аккаунт. */
export async function deleteAccount(): Promise<{ ok: boolean }> {
  return request<undefined, { ok: boolean }>("/api/auth/me", {
    method: "DELETE",
  });
}

/** GET /api/consent — статус согласий гостя/пользователя. */
export async function getConsentStatus(
  guestId?: string | null,
): Promise<ConsentStatusResponse> {
  const path = guestId
    ? `/api/consent?guest_id=${encodeURIComponent(guestId)}`
    : "/api/consent";
  return request<undefined, ConsentStatusResponse>(path);
}

export { ApiClientError };
