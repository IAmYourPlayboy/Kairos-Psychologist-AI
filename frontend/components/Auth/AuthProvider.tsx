"use client";

/**
 * AuthProvider — глобальное состояние авторизации.
 *
 * Хранит User | null + статус загрузки. Источник правды — backend
 * через httpOnly cookies. Мы НЕ держим токены в JS-памяти/localStorage
 * (защита от XSS).
 *
 * При монтировании приложения один раз вызывает GET /api/auth/me:
 * - 200 → user в state, status=authenticated
 * - 401 → user=null, status=unauthenticated
 *
 * Действия (login/register/logout) — методы провайдера, после успеха
 * обновляют state.
 *
 * 401 на других эндпоинтах НЕ обрабатывается здесь — это задача
 * `lib/api.ts` (auto-refresh). См. комментарий ниже.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import * as authApi from "@/lib/auth";
import type { ConsentItem, User } from "@/lib/auth";
import { pullSessionsFromServer } from "@/lib/sessions";

export type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  user: User | null;
  status: AuthStatus;
  /** Войти. Кидает Error при неуспехе, чтобы UI показал toast/inline-ошибку. */
  login: (email: string, password: string) => Promise<void>;
  /** Зарегистрироваться. Кидает Error при неуспехе. */
  register: (input: {
    email: string;
    password: string;
    displayName?: string;
    guestId?: string | null;
    consents?: ConsentItem[];
  }) => Promise<void>;
  /** Выйти. По умолчанию из текущего устройства, ``everywhere`` — со всех. */
  logout: (everywhere?: boolean) => Promise<void>;
  /** Принудительно перепроверить сессию через GET /me. */
  reload: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");
  // Pull сессий с сервера в Dexie делаем ОДИН раз за жизнь компонента
  // (после первой успешной аутентификации). Дальше — синхронизация идёт
  // через обычные /api/chat вызовы.
  const pulledForUser = useRef<string | null>(null);

  const maybePullSessions = useCallback(async (currentUser: User) => {
    if (pulledForUser.current === currentUser.id) return;
    pulledForUser.current = currentUser.id;
    void pullSessionsFromServer();
  }, []);

  const reload = useCallback(async () => {
    try {
      const me = await authApi.getMe();
      setUser(me);
      setStatus("authenticated");
      void maybePullSessions(me);
    } catch {
      setUser(null);
      setStatus("unauthenticated");
      pulledForUser.current = null;
    }
  }, [maybePullSessions]);

  // При монтировании — один раз проверяем наличие сессии.
  useEffect(() => {
    void reload();
  }, [reload]);

  const login = useCallback(
    async (email: string, password: string) => {
      const result = await authApi.login(email, password);
      setUser(result.user);
      setStatus("authenticated");
      void maybePullSessions(result.user);
    },
    [maybePullSessions],
  );

  const register = useCallback(
    async (input: {
      email: string;
      password: string;
      displayName?: string;
      guestId?: string | null;
      consents?: ConsentItem[];
    }) => {
      const result = await authApi.register(input);
      setUser(result.user);
      setStatus("authenticated");
      // На register гостевые сессии уже мигрированы на сервере.
      // Pull тоже делаем — на случай если у юзера были другие устройства.
      void maybePullSessions(result.user);
    },
    [maybePullSessions],
  );

  const logout = useCallback(async (everywhere = false) => {
    await authApi.logout(everywhere);
    setUser(null);
    setStatus("unauthenticated");
    pulledForUser.current = null;
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, status, login, register, logout, reload }),
    [user, status, login, register, logout, reload],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    // Тихий fallback (как в других провайдерах). Не валим, потому что какие-то
    // компоненты могут рендериться вне провайдера (тесты, storybook).
    return {
      user: null,
      status: "loading",
      login: async () => {},
      register: async () => {},
      logout: async () => {},
      reload: async () => {},
    };
  }
  return ctx;
}
