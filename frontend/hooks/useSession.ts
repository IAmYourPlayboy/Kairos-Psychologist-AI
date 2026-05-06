"use client";

import { useSessionContext } from "@/components/Layout/KairosProviders";

/**
 * Хук сессии — обёртка над KairosProviders SessionContext.
 *
 * Все потребители (Sidebar, ChatContainer/useChat, /profile/page) читают
 * одно и то же состояние, поэтому resetSession/switchToSession реально
 * влияют на активную сессию во всём приложении.
 */
export function useSession() {
  return useSessionContext();
}
