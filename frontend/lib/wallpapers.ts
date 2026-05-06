// frontend/lib/wallpapers.ts
/**
 * Список доступных обоев. Все файлы локально в /public/wallpapers/.
 *
 * Никаких внешних URL (ФЗ-152: персональные данные не передаются на иностранные CDN).
 *
 * Thumbnails (если понадобятся в settings-picker) генерируются Next/Image
 * через `sizes` или `?w=200` — не нужно отдельное поле.
 *
 * "none" — специальный id «без обоев». Дефолт. Background при этом не
 * рендерит <Image>, и виден базовый цвет body (warm-50 / neutral-950).
 */

export interface Wallpaper {
  id: string;
  src: string | null; // null = «без обоев», базовый цвет body
  label: string;
}

export const WALLPAPER_NONE_ID = "none";

export const WALLPAPERS: Wallpaper[] = [
  { id: WALLPAPER_NONE_ID, src: null, label: "Без обоев" },
  { id: "forest",    src: "/wallpapers/forest.jpg",    label: "Лес" },
  { id: "mountains", src: "/wallpapers/mountains.jpg", label: "Горы" },
  { id: "ocean",     src: "/wallpapers/ocean.jpg",     label: "Океан" },
  { id: "stars",     src: "/wallpapers/stars.jpg",     label: "Звёзды" },
];

export const DEFAULT_WALLPAPER_ID = WALLPAPER_NONE_ID;

export function getWallpaperById(id: string | null | undefined): Wallpaper {
  if (!id) return WALLPAPERS[0];
  return WALLPAPERS.find((w) => w.id === id) ?? WALLPAPERS[0];
}

/**
 * Удобный helper для UI — есть ли картинка для рендера или это «без обоев».
 */
export function hasWallpaperImage(wp: Wallpaper): boolean {
  return wp.src !== null;
}
