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
