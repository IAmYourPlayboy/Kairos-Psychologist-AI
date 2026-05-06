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
 * Никаких видеообоев, никаких внешних CDN. Только локальные JPG.
 */
export function Background() {
  const { wallpaper } = useWallpaper();
  const t = useThemeTokens();

  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 z-0 overflow-hidden pointer-events-none"
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
