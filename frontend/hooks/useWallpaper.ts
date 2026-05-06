"use client";

import { useCallback, useEffect, useState } from "react";

import {
  DEFAULT_WALLPAPER_ID,
  getWallpaperById,
  type Wallpaper,
} from "@/lib/wallpapers";

const STORAGE_KEY = "kairos.wallpaper-id";

export function useWallpaper() {
  const [wallpaperId, setWallpaperIdState] = useState<string>(DEFAULT_WALLPAPER_ID);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) setWallpaperIdState(saved);
    } catch {
      // тихо
    }
    setMounted(true);
  }, []);

  const setWallpaperId = useCallback((id: string) => {
    setWallpaperIdState(id);
    try {
      localStorage.setItem(STORAGE_KEY, id);
    } catch {
      // тихо
    }
  }, []);

  const wallpaper: Wallpaper = getWallpaperById(wallpaperId);

  return { wallpaperId, wallpaper, setWallpaperId, mounted };
}
