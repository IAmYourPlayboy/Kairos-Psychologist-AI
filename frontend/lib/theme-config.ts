/**
 * Конфигурация авто-определения темы по локальному времени.
 *
 * 21:00–06:59 → тёмная тема при первом визите.
 * Используется в hooks/useTheme.ts и в inline-скрипте ThemeScript.tsx.
 *
 * ⚠ ThemeScript содержит inline JS с захардкоженными числами.
 * Если изменишь значения здесь — синхронизируй и там тоже.
 */
export const DARK_HOUR_START = 21;
export const DARK_HOUR_END = 7;

export const THEME_STORAGE_KEY = "kairos-theme";
