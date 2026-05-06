"use client";

import { useEffect, useState } from "react";

import {
  deleteAllDossier,
  deleteFact,
  fetchDossier,
} from "@/lib/dossierApi";
import type { DossierFact } from "@/lib/types";

/**
 * Просмотр и управление досье пользователя.
 *
 * Группирует факты по папкам, показывает summary + цитаты + severity.
 * Каждый факт можно удалить. Внизу — кнопка «удалить всё досье».
 *
 * MVP: guestId — из useSession. После Блока 13 (auth) — настоящий userId.
 */
interface DossierViewProps {
  guestId: string;
}

export default function DossierView({ guestId }: DossierViewProps) {
  const [facts, setFacts] = useState<DossierFact[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isWiping, setIsWiping] = useState(false);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [guestId]);

  async function load() {
    try {
      const res = await fetchDossier(guestId);
      setFacts(res.facts);
      setError(null);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Не удалось загрузить досье",
      );
    }
  }

  async function handleDeleteFact(factId: string) {
    if (!confirm("Удалить этот факт? Это действие необратимо.")) return;
    try {
      await deleteFact(guestId, factId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка удаления");
    }
  }

  async function handleWipeAll() {
    if (
      !confirm(
        "Удалить ВСЁ досье? Кайрос забудет всё, что узнал о тебе. " +
          "Это действие необратимо.",
      )
    )
      return;
    setIsWiping(true);
    try {
      await deleteAllDossier(guestId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка удаления");
    } finally {
      setIsWiping(false);
    }
  }

  if (error) {
    return (
      <div className="text-crisis-700 p-4 max-w-3xl mx-auto">
        ⚠️ {error}
      </div>
    );
  }

  if (facts === null) {
    return (
      <div className="text-warm-600 p-4 max-w-3xl mx-auto">
        Загружаю досье...
      </div>
    );
  }

  if (facts.length === 0) {
    return (
      <div className="max-w-3xl mx-auto p-4 space-y-4">
        <header className="border-b border-warm-200 pb-4">
          <h1 className="text-xl font-semibold text-warm-900">
            Что знает Кайрос
          </h1>
        </header>
        <div className="text-warm-600">
          Кайрос ещё ничего не запомнил о тебе. Это появится после нескольких
          бесед — обычно через 15 минут после того, как ты замолкаешь, бот
          просматривает разговор и сохраняет важное в досье.
        </div>
      </div>
    );
  }

  // Группировка по папкам (folder/subfolder)
  const byFolder = facts.reduce<Record<string, DossierFact[]>>((acc, f) => {
    const key = f.subfolder ? `${f.folder}/${f.subfolder}` : f.folder;
    (acc[key] ??= []).push(f);
    return acc;
  }, {});

  return (
    <div className="max-w-3xl mx-auto p-4 space-y-6">
      <header className="border-b border-warm-200 pb-4">
        <h1 className="text-xl font-semibold text-warm-900">
          Что знает Кайрос
        </h1>
        <p className="text-sm text-warm-600 mt-1">
          Это всё, что Кайрос запомнил о тебе из ваших разговоров. Ты можешь
          удалить любой факт или всё сразу.
        </p>
      </header>

      {Object.entries(byFolder).map(([folder, folderFacts]) => (
        <section key={folder}>
          <h2 className="text-md font-medium text-warm-800 mb-2">
            {folder}
          </h2>
          <div className="space-y-3">
            {folderFacts.map((f) => (
              <article
                key={f.id}
                className={`bg-warm-50 border rounded-lg p-4 ${
                  f.superseded
                    ? "border-warm-300 opacity-60"
                    : "border-warm-200"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <p className="text-warm-900">
                      {f.superseded && (
                        <span className="text-xs text-warm-500 mr-2">
                          [устарело]
                        </span>
                      )}
                      {f.summary}
                    </p>
                    {f.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {f.tags.map((tag) => (
                          <span
                            key={tag}
                            className="text-xs px-2 py-0.5 bg-warm-200 text-warm-800 rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="text-xs text-warm-500 mt-2">
                      severity: {f.severity.toFixed(2)} · упомянуто{" "}
                      {f.times_mentioned} раз
                    </div>
                    {f.quotes.length > 0 && (
                      <details className="mt-2">
                        <summary className="text-xs text-warm-600 cursor-pointer">
                          Цитаты ({f.quotes.length})
                        </summary>
                        <ul className="mt-2 space-y-1 text-sm text-warm-700 italic">
                          {f.quotes.map((q, i) => (
                            <li key={i}>«{q.text}»</li>
                          ))}
                        </ul>
                      </details>
                    )}
                  </div>
                  <button
                    onClick={() => handleDeleteFact(f.id)}
                    className="text-xs text-crisis-700 hover:text-crisis-900 px-2 py-1"
                    aria-label="Удалить этот факт"
                  >
                    Удалить
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      ))}

      <div className="border-t border-warm-200 pt-4">
        <button
          onClick={handleWipeAll}
          disabled={isWiping}
          className="px-4 py-2 bg-crisis-100 hover:bg-crisis-200 text-crisis-900 rounded-lg text-sm font-medium disabled:opacity-50"
        >
          {isWiping ? "Удаляю..." : "Удалить всё досье"}
        </button>
        <p className="text-xs text-warm-500 mt-2">
          После удаления Кайрос забудет всё, что знал о тебе. Это нельзя
          отменить.
        </p>
      </div>
    </div>
  );
}
