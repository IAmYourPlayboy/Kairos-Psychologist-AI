"use client";

import { useThemeContext } from "@/components/Layout/KairosProviders";

export type { Theme } from "@/components/Layout/KairosProviders";

/**
 * Хук темы — обёртка над KairosProviders ThemeContext.
 *
 * Все потребители (ThemeToggle, AppShell, useThemeTokens, settings page)
 * читают одно и то же состояние через единый провайдер.
 */
export function useTheme() {
  return useThemeContext();
}
