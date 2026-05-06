/**
 * Inline-скрипт, который выставляет класс `.dark` на <html> ДО гидратации React.
 * Это предотвращает «вспышку светлой темы» при первой загрузке.
 *
 * ⚠ SYNC POINT: this inline script duplicates logic from hooks/useTheme.ts.
 * If you change DARK_HOUR_START / DARK_HOUR_END / THEME_STORAGE_KEY in
 * lib/theme-config.ts — UPDATE THE INLINE SCRIPT BELOW TO MATCH.
 *
 * The inline script must stay literal (no imports) because it runs before
 * React hydration and must be self-contained in <head>.
 *
 * Подключается в <head> в app/layout.tsx первым ребёнком.
 */
export function ThemeScript() {
  const code = `
(function() {
  try {
    var saved = null;
    try { saved = localStorage.getItem('kairos-theme'); } catch (e) {}
    var theme = (saved === 'dark' || saved === 'light') ? saved : null;
    if (!theme) {
      var h = new Date().getHours();
      theme = (h >= 21 || h < 7) ? 'dark' : 'light';
    }
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    }
  } catch (e) {}
})();
  `.trim();
  return <script dangerouslySetInnerHTML={{ __html: code }} />;
}
