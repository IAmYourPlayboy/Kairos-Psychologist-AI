"use client";

/**
 * useAuth — хук состояния авторизации.
 *
 * Тонкая обёртка над AuthProvider. Все потребители получают одно и то же
 * состояние (user, status), методы login/register/logout/reload.
 */

export { useAuth } from "@/components/Auth/AuthProvider";
export type { User, ConsentItem } from "@/lib/auth";
