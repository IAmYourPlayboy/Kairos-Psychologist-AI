"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Lightbulb, X } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/hooks/useThemeTokens";
import { getTipOfTheDay } from "@/lib/tips";

const STORAGE_KEY = "kairos.tip-dismissed-day";

function getDayKey(): string {
  const now = new Date();
  return `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`;
}

/**
 * Плавающая карточка «Совет дня» в правом доке.
 * Закрывается × → не показывается до следующего дня.
 *
 * Видимость определяется только после маунта (mounted флаг) —
 * иначе SSR-рендер не совпадал бы с клиентским и React выдавал бы
 * hydration mismatch.
 */
export function TipCard() {
  const t = useThemeTokens();
  const tip = getTipOfTheDay();

  const [mounted, setMounted] = useState(false);
  const [isDismissedToday, setIsDismissedToday] = useState(false);

  useEffect(() => {
    try {
      setIsDismissedToday(localStorage.getItem(STORAGE_KEY) === getDayKey());
    } catch {
      setIsDismissedToday(false);
    }
    setMounted(true);
  }, []);

  const handleDismiss = () => {
    setIsDismissedToday(true);
    try {
      localStorage.setItem(STORAGE_KEY, getDayKey());
    } catch {
      // тихо
    }
  };

  // До маунта рендерим пустоту — никаких визуальных артефактов на гидрации.
  if (!mounted) return null;

  return (
    <AnimatePresence>
      {!isDismissedToday && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95, height: 0 }}
          animate={{ opacity: 1, scale: 1, height: "auto" }}
          exit={{ opacity: 0, scale: 0.95, height: 0, filter: "blur(4px)" }}
          transition={{ duration: 0.3 }}
          className="w-[200px] mt-4 overflow-hidden pointer-events-auto"
        >
          <Card className={cn("backdrop-blur-3xl rounded-3xl relative", t.tipCard)}>
            <Button
              size="icon"
              variant="ghost"
              onClick={handleDismiss}
              aria-label="Закрыть совет дня"
              className={cn(
                "absolute right-2 top-2 size-6 rounded-full z-10",
                t.tipCloseBtn,
              )}
            >
              <X className="size-3" />
            </Button>
            <CardHeader className="flex flex-col items-start gap-2 pb-2 pt-4 px-4">
              <div
                className={cn(
                  "size-8 rounded-xl flex items-center justify-center shadow-inner shrink-0",
                  t.tipIcon,
                )}
              >
                <Lightbulb className="size-4" />
              </div>
              <div className="font-semibold text-[13px] leading-tight">
                Совет дня
              </div>
            </CardHeader>
            <CardContent className="px-4 pb-4 pt-0">
              <p className="text-[12px] leading-[1.5] font-medium opacity-90">
                {tip.text}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
