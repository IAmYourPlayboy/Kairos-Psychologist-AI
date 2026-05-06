"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "kairos-theme";

export type Theme = "dark" | "light";

/**
 * Определить начальную тему: сохранённая в localStorage > авто по часу.
 * Авто: 21:00–06:59 локального времени → dark, иначе → light.
 *
 * Срабатывает только в браузере. На сервере возвращает "light"
 * (anti-flash скрипт в <head> применит правильный класс до гидратации).
 */
function detectInitialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "dark" || saved === "light") return saved;
  } catch {
    // localStorage недоступен (приватный режим) — fallback на авто
  }
  const hour = new Date().getHours();
  return hour >= 21 || hour < 7 ? "dark" : "light";
}

/**
 * Хук темы: возвращает theme + isDark + toggle.
 * При смене темы обновляет класс `.dark` на <html> и сохраняет в localStorage.
 */
export function useTheme() {
  const [theme, setThemeState] = useState<Theme>("light");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const initial = detectInitialTheme();
    setThemeState(initial);
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    document.documentElement.classList.toggle("dark", theme === "dark");
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // тихо игнорируем
    }
  }, [theme, mounted]);

  const toggle = useCallback(() => {
    setThemeState((t) => (t === "dark" ? "light" : "dark"));
  }, []);

  const setTheme = useCallback((next: Theme) => {
    setThemeState(next);
  }, []);

  return { theme, isDark: theme === "dark", toggle, setTheme, mounted };
}
