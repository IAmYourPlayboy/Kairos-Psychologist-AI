/**
 * API-обёртка для досье пользователя.
 *
 * MVP: используем guest_id из useSession, бэкенд резолвит в реальный user_id
 * через привязанные ChatSession. После Блока 13 (auth) — пользователь будет
 * настоящий, и параметр поменяется на JWT cookie.
 */

import { ApiClientError } from "./api";
import type {
  DossierDeleteResponse,
  DossierResponse,
} from "./types";

async function jsonRequest<T>(
  url: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(url, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  let data: unknown;
  try {
    data = await res.json();
  } catch {
    throw new ApiClientError({
      type: "non_json_response",
      status: res.status,
      message: `Сервер вернул не-JSON (${res.status})`,
    });
  }
  if (!res.ok) {
    const apiError = (data as { error?: { type: string; status: number; message: string } }).error;
    throw new ApiClientError(
      apiError ?? {
        type: "unknown",
        status: res.status,
        message: `HTTP ${res.status}`,
      },
    );
  }
  return data as T;
}

export async function fetchDossier(guestId: string): Promise<DossierResponse> {
  return jsonRequest(`/api/dossier?guest_id=${encodeURIComponent(guestId)}`);
}

export async function deleteFact(
  guestId: string,
  factId: string,
): Promise<DossierDeleteResponse> {
  return jsonRequest(
    `/api/dossier/${encodeURIComponent(factId)}?guest_id=${encodeURIComponent(guestId)}`,
    { method: "DELETE" },
  );
}

export async function deleteAllDossier(
  guestId: string,
): Promise<DossierDeleteResponse> {
  return jsonRequest(
    `/api/dossier?guest_id=${encodeURIComponent(guestId)}`,
    { method: "DELETE" },
  );
}
