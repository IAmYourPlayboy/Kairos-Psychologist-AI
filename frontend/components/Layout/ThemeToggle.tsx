"use client";

import { motion } from "motion/react";
import { Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { useTheme } from "@/hooks/useTheme";
import { useThemeTokens } from "@/hooks/useThemeTokens";

/**
 * Кнопка переключения темы. Размещается в RightDock.
 * Иконка крутится при смене (motion).
 */
export function ThemeToggle() {
  const { isDark, toggle, mounted } = useTheme();
  const t = useThemeTokens();

  if (!mounted) return <div className="size-11" aria-hidden="true" />;

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggle}
      aria-label={isDark ? "Включить светлую тему" : "Включить тёмную тему"}
      className={cn(
        "rounded-full size-11 backdrop-blur-xl transition-all duration-300 hover:scale-110 active:scale-90 border-none",
        t.glassSidebar,
        t.textMain,
        t.btnHover,
      )}
    >
      <motion.div
        initial={false}
        animate={{ rotate: isDark ? 0 : 90, scale: isDark ? 1 : 1.1 }}
        transition={{ duration: 0.4, ease: "backOut" }}
      >
        {isDark ? <Moon className="size-5" /> : <Sun className="size-5" />}
      </motion.div>
    </Button>
  );
}
