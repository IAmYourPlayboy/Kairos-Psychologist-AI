"use client";

import { useSidebarContext } from "@/components/Layout/KairosProviders";

/**
 * Хук сайдбара — обёртка над KairosProviders SidebarContext.
 *
 * Все потребители (FloatingButtons, Sidebar, ChatContainer) читают одно
 * и то же состояние через единый провайдер.
 */
export function useSidebar() {
  return useSidebarContext();
}
