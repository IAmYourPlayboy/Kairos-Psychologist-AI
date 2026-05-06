"use client";

import { useCallback, useEffect, useState } from "react";

import {
  deleteSession as dbDeleteSession,
  listSessions,
  type LocalSession,
} from "@/lib/db";

/**
 * Список сессий пользователя/гостя.
 *
 * MVP: источник — локальный Dexie. Пока бэкенд-эндпоинты GET/PATCH/DELETE
 * /api/sessions не появились (Блок ~16 PROGRESS.md).
 *
 * Когда появятся — переключаем `loadSessions` на API и оставляем Dexie
 * только как офлайн-кэш. UI не меняется.
 */

export interface SessionMeta {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

const TITLE_STORAGE_KEY = "kairos.session-titles";

function readTitles(): Record<string, string> {
  if (typeof window === "undefined") return {};
  try {
    const raw = localStorage.getItem(TITLE_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Record<string, string>) : {};
  } catch {
    return {};
  }
}

function writeTitles(map: Record<string, string>) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(TITLE_STORAGE_KEY, JSON.stringify(map));
  } catch {
    // тихо
  }
}

function defaultTitle(s: LocalSession): string {
  const date = new Date(s.createdAt);
  return `Беседа ${date.toLocaleDateString("ru-RU", { day: "numeric", month: "short" })}`;
}

export function useSessions() {
  const [sessions, setSessions] = useState<SessionMeta[] | null>(null);

  const reload = useCallback(async () => {
    const local = await listSessions(50);
    const titles = readTitles();
    const meta: SessionMeta[] = local.map((s) => ({
      id: s.id,
      title: titles[s.id] ?? defaultTitle(s),
      createdAt: s.createdAt,
      updatedAt: s.updatedAt,
      messageCount: s.messageCount,
    }));
    setSessions(meta);
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const renameSession = useCallback(
    async (id: string, title: string) => {
      const titles = readTitles();
      titles[id] = title;
      writeTitles(titles);
      await reload();
    },
    [reload],
  );

  const deleteSession = useCallback(
    async (id: string) => {
      await dbDeleteSession(id);
      const titles = readTitles();
      delete titles[id];
      writeTitles(titles);
      await reload();
    },
    [reload],
  );

  return { sessions, reload, renameSession, deleteSession };
}
