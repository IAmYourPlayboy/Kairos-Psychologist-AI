"use client";

import Image from "next/image";

import { cn } from "@/lib/cn";
import { useThemeTokens } from "@/hooks/useThemeTokens";
import { useWallpaper } from "@/hooks/useWallpaper";

/**
 * Слой фона: одна большая картинка + темовый overlay.
 *
 * Картинка статичная, через next/image для оптимизации.
 * Overlay меняется по теме (dark — bg-black/50, light — bg-white/20)
 * через useThemeTokens.
 *
 * mounted-guard: до рендера на клиенте мы не знаем, какие обои выбрал
 * пользователь (значение в localStorage). Чтобы не показывать default
 * пока загружаем настоящие — рендерим только overlay до маунта.
 *
 * Никаких видеообоев, никаких внешних CDN. Только локальные JPG.
 */
export function Background() {
  const { wallpaper, mounted } = useWallpaper();
  const t = useThemeTokens();

  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 z-decorative overflow-hidden pointer-events-none"
    >
      {mounted && (
        <Image
          key={wallpaper.id}
          src={wallpaper.src}
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover scale-105 transition-transform duration-[20s] ease-linear"
        />
      )}
      <div className={cn("absolute inset-0 transition-colors duration-700", t.overlay)} />
    </div>
  );
}
