"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "kairos.sidebar-open";

/**
 * Хук для управления состоянием левого сайдбара (открыт/свёрнут).
 *
 * Persist в localStorage. На мобильных по умолчанию закрыт
 * (определяется по window.matchMedia при первом маунте).
 */
export function useSidebar() {
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    let initial: boolean;
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "true" || saved === "false") {
        initial = saved === "true";
      } else {
        // Первый визит: на мобильных закрыт, на десктопе открыт.
        initial = window.matchMedia("(min-width: 768px)").matches;
      }
    } catch {
      initial = window.matchMedia("(min-width: 768px)").matches;
    }
    setIsOpen(initial);
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    try {
      localStorage.setItem(STORAGE_KEY, String(isOpen));
    } catch {
      // тихо
    }
  }, [isOpen, mounted]);

  const toggle = useCallback(() => setIsOpen((v) => !v), []);
  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);

  return { isOpen, toggle, open, close, mounted };
}
