"use client";

import { useRouter, usePathname } from "next/navigation";
import { motion } from "motion/react";
import { PanelLeft, Settings as SettingsIcon } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { SIDEBAR_WIDTH } from "@/components/Layout/Sidebar";
import { cn } from "@/lib/cn";
import { useSidebar } from "@/hooks/useSidebar";
import { useThemeTokens } from "@/hooks/useThemeTokens";

/**
 * Две плавающие кнопки в левом нижнем углу:
 *  - Settings — открыть/закрыть страницу /settings
 *  - PanelLeft — свернуть/развернуть сайдбар
 *
 * Положение анимируется в зависимости от того, открыт ли сайдбар:
 *  - открыт: настройки слева внизу, тоггл — у правого края сайдбара
 *  - закрыт: и тоггл, и настройки оба в левом нижнем углу (стэк)
 */
export function FloatingButtons() {
  const t = useThemeTokens();
  const router = useRouter();
  const pathname = usePathname();
  const { isOpen, toggle } = useSidebar();

  const isOnSettings = pathname.startsWith("/settings");

  return (
    <div
      className="absolute bottom-6 left-0 h-12 z-floating-high pointer-events-none"
      style={{ width: SIDEBAR_WIDTH }}
    >
      {/* Кнопка настроек */}
      <motion.div
        initial={false}
        animate={{ x: 16, y: isOpen ? 0 : -52 }}
        transition={{ type: "spring", bounce: 0.25, duration: 0.6 }}
        className="absolute pointer-events-auto"
      >
        <Button
          variant="ghost"
          size="icon"
          aria-label={isOnSettings ? "Закрыть настройки" : "Открыть настройки"}
          className={cn("size-10 rounded-full", t.floatingBtn, isOnSettings && "ring-2 ring-accent-400")}
          onClick={() => router.push(isOnSettings ? "/chat" : "/settings")}
        >
          <motion.div
            className="size-full flex items-center justify-center"
            whileHover={{ rotate: 90 }}
            transition={{ duration: 0.4 }}
          >
            <SettingsIcon className="size-5" />
          </motion.div>
        </Button>
      </motion.div>

      {/* Кнопка toggle сайдбара */}
      <motion.div
        initial={false}
        animate={{
          x: isOpen ? SIDEBAR_WIDTH - 16 - 40 : 16,
          y: 0,
        }}
        transition={{ type: "spring", bounce: 0.25, duration: 0.6 }}
        className="absolute pointer-events-auto"
      >
        <Button
          variant="ghost"
          size="icon"
          aria-label={isOpen ? "Свернуть сайдбар" : "Развернуть сайдбар"}
          className={cn("size-10 rounded-xl", t.floatingBtn)}
          onClick={toggle}
        >
          <motion.div
            className="size-full flex items-center justify-center"
            whileHover={{ x: -2 }}
            transition={{ type: "spring", bounce: 0.5 }}
          >
            <PanelLeft className="size-5" />
          </motion.div>
        </Button>
      </motion.div>
    </div>
  );
}
