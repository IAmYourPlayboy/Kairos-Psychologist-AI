"use client";

import Image from "next/image";
import { motion, useReducedMotion } from "motion/react";
import { Check, Moon, Settings as SettingsIcon, Sun } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { cn, RIGHT_DOCK_PADDING } from "@/lib/cn";
import { useTheme } from "@/hooks/useTheme";
import { useThemeTokens } from "@/hooks/useThemeTokens";
import { useWallpaper } from "@/hooks/useWallpaper";
import { WALLPAPERS } from "@/lib/wallpapers";

/**
 * Минимальная страница настроек: тема + обои.
 *
 * Полные настройки (уведомления, режим тишины, профиль заботы,
 * стиль общения) — после MVP, в отдельной сессии.
 */
export default function SettingsPage() {
  const t = useThemeTokens();
  const { isDark, setTheme } = useTheme();
  const { wallpaperId, setWallpaperId } = useWallpaper();
  const shouldReduceMotion = useReducedMotion();

  return (
    <div className={cn("flex-1 w-full overflow-y-auto custom-scrollbar p-4 sm:p-6 lg:p-12", RIGHT_DOCK_PADDING)}>
      <div className="max-w-3xl mx-auto space-y-8 pb-10">
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={shouldReduceMotion ? { duration: 0 } : undefined}
          className="flex items-center gap-4"
        >
          <div
            className={cn(
              "size-12 rounded-2xl flex items-center justify-center shadow-lg backdrop-blur-xl border",
              t.glassSidebar,
              t.textMain,
            )}
          >
            <SettingsIcon className="size-6" />
          </div>
          <div>
            <h1 className={cn("text-2xl font-semibold tracking-tight", t.textMain)}>
              Настройки
            </h1>
            <p className={cn("text-sm mt-1", t.textMuted)}>
              Тема и обои. Остальные настройки появятся позже.
            </p>
          </div>
        </motion.div>

        {/* Тема */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={shouldReduceMotion ? { duration: 0 } : { delay: 0.05 }}
        >
          <Card className={cn(t.glassPanel, "p-5")}>
            <h2 className={cn("font-medium mb-3", t.textMain)}>Тема</h2>
            <div className="flex gap-2">
              <Button
                variant="ghost"
                onClick={() => setTheme("light")}
                aria-label="Светлая тема"
                aria-pressed={!isDark}
                className={cn(
                  "flex-1 gap-2",
                  t.btnHover,
                  !isDark
                    ? "bg-white/40 dark:bg-white/15 ring-2 ring-accent-400"
                    : "",
                )}
              >
                <Sun className="size-4" /> Светлая
              </Button>
              <Button
                variant="ghost"
                onClick={() => setTheme("dark")}
                aria-label="Тёмная тема"
                aria-pressed={isDark}
                className={cn(
                  "flex-1 gap-2",
                  t.btnHover,
                  isDark
                    ? "bg-white/15 ring-2 ring-accent-400"
                    : "",
                )}
              >
                <Moon className="size-4" /> Тёмная
              </Button>
            </div>
          </Card>
        </motion.div>

        {/* Обои */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={shouldReduceMotion ? { duration: 0 } : { delay: 0.1 }}
        >
          <Card className={cn(t.glassPanel, "p-5")}>
            <h2 className={cn("font-medium mb-3", t.textMain)}>Обои</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {WALLPAPERS.map((wp) => {
                const isActive = wallpaperId === wp.id;
                return (
                  <button
                    key={wp.id}
                    type="button"
                    onClick={() => setWallpaperId(wp.id)}
                    aria-label={`Выбрать обои "${wp.label}"`}
                    aria-pressed={isActive}
                    className={cn(
                      "relative aspect-video rounded-xl overflow-hidden border-2 transition-all duration-300 group",
                      isActive
                        ? "border-accent-400 shadow-[0_0_15px_rgba(125,179,194,0.5)]"
                        : "border-transparent hover:border-white/50",
                    )}
                  >
                    <Image
                      src={wp.src}
                      alt={wp.label}
                      fill
                      sizes="(max-width: 640px) 50vw, 25vw"
                      className="object-cover transition-transform duration-500 group-hover:scale-110"
                    />
                    {isActive && (
                      <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
                        <div className="bg-accent-500 text-white rounded-full p-1.5 shadow-lg">
                          <Check className="size-5" />
                        </div>
                      </div>
                    )}
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2">
                      <span className="text-xs text-white font-medium">
                        {wp.label}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
