// frontend/lib/wallpapers.ts
/**
 * Список доступных обоев. Все файлы локально в /public/wallpapers/.
 *
 * Никаких внешних URL (ФЗ-152: персональные данные не передаются на иностранные CDN).
 */

export interface Wallpaper {
  id: string;
  src: string; // относительный путь от /public
  thumbSrc: string; // тот же файл (Next/Image сам сделает thumbnail)
  label: string;
}

export const WALLPAPERS: Wallpaper[] = [
  { id: "forest",    src: "/wallpapers/forest.jpg",    thumbSrc: "/wallpapers/forest.jpg",    label: "Лес" },
  { id: "mountains", src: "/wallpapers/mountains.jpg", thumbSrc: "/wallpapers/mountains.jpg", label: "Горы" },
  { id: "ocean",     src: "/wallpapers/ocean.jpg",     thumbSrc: "/wallpapers/ocean.jpg",     label: "Океан" },
  { id: "stars",     src: "/wallpapers/stars.jpg",     thumbSrc: "/wallpapers/stars.jpg",     label: "Звёзды" },
];

export const DEFAULT_WALLPAPER_ID = "forest";

export function getWallpaperById(id: string | null | undefined): Wallpaper {
  if (!id) return WALLPAPERS[0];
  return WALLPAPERS.find((w) => w.id === id) ?? WALLPAPERS[0];
}
