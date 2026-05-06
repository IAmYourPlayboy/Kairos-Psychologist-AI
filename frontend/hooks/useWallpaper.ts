"use client";

import { useWallpaperContext } from "@/components/Layout/KairosProviders";

/**
 * Хук обоев — обёртка над KairosProviders WallpaperContext.
 *
 * Все потребители (Background, Settings page) читают одно и то же
 * состояние, поэтому setWallpaperId() реально влияет на фон во всём
 * приложении, не только в той странице где вызвали.
 */
export function useWallpaper() {
  return useWallpaperContext();
}
