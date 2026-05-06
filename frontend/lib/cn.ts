// frontend/lib/cn.ts
/**
 * Утилита для объединения Tailwind-классов:
 * - clsx собирает условные классы
 * - tailwind-merge корректно резолвит конфликты (например, p-4 + p-2 → p-2)
 *
 * Пример:
 *   cn("px-4 py-2", isActive && "bg-blue-500", "px-6")
 *   // → "py-2 bg-blue-500 px-6"
 */
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Tailwind classes для правого padding'а контентной области, оставляющего место
 * под RightDock (260px / 280px на md/lg). Используется на всех страницах,
 * рендерящихся внутри AppShell.
 */
export const RIGHT_DOCK_PADDING = "md:pr-[260px] lg:pr-[280px]";
