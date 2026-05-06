// frontend/lib/wallpapers.ts
/**
 * Список доступных обоев. Все файлы локально в /public/wallpapers/.
 *
 * Никаких внешних URL (ФЗ-152: персональные данные не передаются на иностранные CDN).
 *
 * Thumbnails (если понадобятся в settings-picker) генерируются Next/Image
 * через `sizes` или `?w=200` — не нужно отдельное поле.
 */

export interface Wallpaper {
  id: string;
  src: string; // относительный путь от /public
  label: string;
}

export const WALLPAPERS: Wallpaper[] = [
  { id: "forest",    src: "/wallpapers/forest.jpg",    label: "Лес" },
  { id: "mountains", src: "/wallpapers/mountains.jpg", label: "Горы" },
  { id: "ocean",     src: "/wallpapers/ocean.jpg",     label: "Океан" },
  { id: "stars",     src: "/wallpapers/stars.jpg",     label: "Звёзды" },
];

export const DEFAULT_WALLPAPER_ID = "forest";

export function getWallpaperById(id: string | null | undefined): Wallpaper {
  if (!id) return WALLPAPERS[0];
  return WALLPAPERS.find((w) => w.id === id) ?? WALLPAPERS[0];
}
