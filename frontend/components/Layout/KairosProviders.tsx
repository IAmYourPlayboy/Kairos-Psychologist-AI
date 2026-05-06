"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  DARK_HOUR_END,
  DARK_HOUR_START,
  THEME_STORAGE_KEY,
} from "@/lib/theme-config";

// ============================================================================
// THEME CONTEXT
// ============================================================================

export type Theme = "dark" | "light";

interface ThemeContextValue {
  theme: Theme;
  isDark: boolean;
  toggle: () => void;
  setTheme: (next: Theme) => void;
  mounted: boolean;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function detectInitialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  try {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    if (saved === "dark" || saved === "light") return saved;
  } catch {
    // localStorage недоступен (приватный режим) — fallback на авто
  }
  const hour = new Date().getHours();
  return hour >= DARK_HOUR_START || hour < DARK_HOUR_END ? "dark" : "light";
}

function ThemeProvider({ children }: { children: ReactNode }) {
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
      localStorage.setItem(THEME_STORAGE_KEY, theme);
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

  const value = useMemo<ThemeContextValue>(
    () => ({ theme, isDark: theme === "dark", toggle, setTheme, mounted }),
    [theme, toggle, setTheme, mounted],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useThemeContext(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    // Тихий fallback: если хук вызвали вне провайдера — возвращаем стабильные дефолты,
    // чтобы не падать. На практике означает что компонент рендерится вне KairosProviders.
    return {
      theme: "light",
      isDark: false,
      toggle: () => {},
      setTheme: () => {},
      mounted: false,
    };
  }
  return ctx;
}

// ============================================================================
// SIDEBAR CONTEXT
// ============================================================================

const SIDEBAR_STORAGE_KEY = "kairos.sidebar-open";

interface SidebarContextValue {
  isOpen: boolean;
  toggle: () => void;
  open: () => void;
  close: () => void;
  mounted: boolean;
}

const SidebarContext = createContext<SidebarContextValue | null>(null);

function SidebarProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    let initial: boolean;
    try {
      const saved = localStorage.getItem(SIDEBAR_STORAGE_KEY);
      if (saved === "true" || saved === "false") {
        initial = saved === "true";
      } else {
        // Первый визит: на мобильных закрыт, на десктопе открыт
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
      localStorage.setItem(SIDEBAR_STORAGE_KEY, String(isOpen));
    } catch {
      // тихо
    }
  }, [isOpen, mounted]);

  const toggle = useCallback(() => setIsOpen((v) => !v), []);
  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);

  const value = useMemo<SidebarContextValue>(
    () => ({ isOpen, toggle, open, close, mounted }),
    [isOpen, toggle, open, close, mounted],
  );

  return (
    <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>
  );
}

export function useSidebarContext(): SidebarContextValue {
  const ctx = useContext(SidebarContext);
  if (!ctx) {
    return {
      isOpen: false,
      toggle: () => {},
      open: () => {},
      close: () => {},
      mounted: false,
    };
  }
  return ctx;
}

// ============================================================================
// SESSION CONTEXT
// ============================================================================

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

interface SessionContextValue {
  guestId: string | null;
  sessionId: string | null;
  resetSession: () => void;
  switchToSession: (id: string) => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

function SessionProvider({ children }: { children: ReactNode }) {
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

  const value = useMemo<SessionContextValue>(
    () => ({ guestId, sessionId, resetSession, switchToSession }),
    [guestId, sessionId, resetSession, switchToSession],
  );

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

export function useSessionContext(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    return {
      guestId: null,
      sessionId: null,
      resetSession: () => {},
      switchToSession: () => {},
    };
  }
  return ctx;
}

// ============================================================================
// COMBINED PROVIDER
// ============================================================================

/**
 * Корневой провайдер для трёх связанных Context'ов: theme / sidebar / session.
 *
 * Зачем нужен: до этой версии useTheme, useSidebar, useSession использовали
 * локальный useState. Каждый вызов создавал ОТДЕЛЬНОЕ состояние, поэтому
 * ThemeToggle.toggle() менял локальный state, но AppShell его не видел —
 * у него было своё состояние. Аналогично для сайдбара и сессий.
 *
 * Решение: вынести state в Context (один раз создаётся, все читают).
 * Монтируется в frontend/app/layout.tsx, оборачивает <AppShell>.
 */
export function KairosProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <SidebarProvider>
        <SessionProvider>{children}</SessionProvider>
      </SidebarProvider>
    </ThemeProvider>
  );
}
