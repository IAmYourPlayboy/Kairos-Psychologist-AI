"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { Folder, ShieldAlert, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/hooks/useThemeTokens";
import {
  deleteAllDossier,
  deleteFact,
  fetchDossier,
} from "@/lib/dossierApi";
import type { DossierFact } from "@/lib/types";

interface DossierViewProps {
  guestId: string;
}

/**
 * Просмотр и управление досье. Логика та же, что была:
 * fetch / delete fact / wipe all. Стиль — glassmorphism, motion-анимации,
 * темовые токены.
 */
export default function DossierView({ guestId }: DossierViewProps) {
  const t = useThemeTokens();
  const shouldReduceMotion = useReducedMotion();
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
      <div className="max-w-3xl mx-auto p-4">
        <Card className={cn(t.glassPanel, "p-4 text-crisis-500")}>
          ⚠️ {error}
        </Card>
      </div>
    );
  }

  if (facts === null) {
    return (
      <div className={cn("max-w-3xl mx-auto p-4", t.textMuted)}>
        Загружаю досье...
      </div>
    );
  }

  if (facts.length === 0) {
    return (
      <div className="max-w-3xl mx-auto p-4 space-y-4">
        <header>
          <h1 className={cn("text-xl font-semibold", t.textMain)}>
            Что знает Кайрос
          </h1>
        </header>
        <Card className={cn(t.glassPanel, "p-6")}>
          <p className={cn("leading-relaxed", t.textMuted)}>
            Кайрос ещё ничего не запомнил о тебе. Это появится после нескольких
            бесед — обычно через 15 минут после того, как ты замолкаешь, бот
            просматривает разговор и сохраняет важное в досье.
          </p>
        </Card>
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
      <motion.header
        initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={shouldReduceMotion ? { duration: 0 } : undefined}
      >
        <h1 className={cn("text-2xl font-semibold tracking-tight", t.textMain)}>
          Что знает Кайрос
        </h1>
        <p className={cn("text-sm mt-1", t.textMuted)}>
          Это всё, что Кайрос запомнил о тебе из ваших разговоров. Ты можешь
          удалить любой факт или всё сразу.
        </p>
      </motion.header>

      {Object.entries(byFolder).map(([folder, folderFacts], folderIdx) => (
        <motion.section
          key={folder}
          initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={shouldReduceMotion ? { duration: 0 } : { delay: folderIdx * 0.05 }}
        >
          <div className="flex items-center gap-2 mb-2">
            <Folder className={cn("size-4", t.textMuted)} />
            <h2 className={cn("text-md font-medium", t.textMain)}>{folder}</h2>
          </div>
          <div className="space-y-2.5">
            {folderFacts.map((f) => (
              <Card
                key={f.id}
                className={cn(
                  t.glassPanel,
                  "p-4 transition-opacity",
                  f.superseded && "opacity-60",
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <p className={cn("leading-relaxed", t.textMain)}>
                      {f.superseded && (
                        <span className={cn("text-xs mr-2", t.textMuted)}>
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
                            className={cn(
                              "text-xs px-2 py-0.5 rounded-md",
                              t.glassSidebar,
                              t.textMuted,
                            )}
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className={cn("text-xs mt-2", t.textMuted)}>
                      severity: {f.severity.toFixed(2)} · упомянуто{" "}
                      {f.times_mentioned} раз
                    </div>
                    {f.quotes.length > 0 && (
                      <details className="mt-2">
                        <summary
                          className={cn("text-xs cursor-pointer", t.textMuted)}
                        >
                          Цитаты ({f.quotes.length})
                        </summary>
                        <ul className={cn("mt-2 space-y-1 text-sm italic", t.textMain)}>
                          {f.quotes.map((q, i) => (
                            <li key={i}>«{q.text}»</li>
                          ))}
                        </ul>
                      </details>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteFact(f.id)}
                    aria-label="Удалить этот факт"
                    className="text-crisis-500 hover:bg-crisis-500/10"
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </motion.section>
      ))}

      <Card className={cn(t.glassPanel, "p-4 mt-6 border-crisis-500/20")}>
        <div className="flex items-start gap-3">
          <div className="size-9 rounded-full bg-crisis-500/15 text-crisis-500 flex items-center justify-center shrink-0">
            <ShieldAlert className="size-4" />
          </div>
          <div className="flex-1">
            <h3 className={cn("font-medium mb-1", t.textMain)}>
              Удалить всё досье
            </h3>
            <p className={cn("text-xs mb-3", t.textMuted)}>
              После удаления Кайрос забудет всё, что знал о тебе. Это нельзя
              отменить.
            </p>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleWipeAll}
              disabled={isWiping}
            >
              {isWiping ? "Удаляю..." : "Удалить всё досье"}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
