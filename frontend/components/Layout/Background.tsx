"use client";

import Image from "next/image";

import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/hooks/useThemeTokens";
import { useWallpaper } from "@/hooks/useWallpaper";

/**
 * Слой фона: опциональная картинка + темовый overlay.
 *
 * По умолчанию обоев НЕТ — виден базовый цвет body (warm-50 / neutral-950).
 * Пользователь выбирает обои в /settings; Background рендерит <Image>
 * только если wallpaper.src !== null.
 *
 * Overlay (полупрозрачный поверх картинки) включаем тоже только когда
 * есть картинка — без неё overlay перекрашивал бы базовый цвет body
 * и делал тёмную тему светлее, что нам не нужно.
 *
 * Никаких видеообоев, никаких внешних CDN. Только локальные JPG.
 */
export function Background() {
  const { wallpaper, mounted } = useWallpaper();
  const t = useThemeTokens();

  // Если выбран «Без обоев» (wallpaper.src === null) — ничего не рендерим.
  // Базовый цвет body (warm-50 light / neutral-950 dark) виден напрямую.
  if (!mounted || wallpaper.src === null) {
    return null;
  }

  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 z-decorative overflow-hidden pointer-events-none"
    >
      <Image
        key={wallpaper.id}
        src={wallpaper.src}
        alt=""
        fill
        priority
        sizes="100vw"
        className="object-cover scale-105 transition-transform duration-[20s] ease-linear"
      />
      <div className={cn("absolute inset-0 transition-colors duration-700", t.overlay)} />
    </div>
  );
}
