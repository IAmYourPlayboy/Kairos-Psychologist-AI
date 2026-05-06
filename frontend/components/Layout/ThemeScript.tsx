/**
 * Inline-скрипт, который выставляет класс `.dark` на <html> ДО гидратации React.
 * Это предотвращает «вспышку светлой темы» при первой загрузке.
 *
 * Логика идентична detectInitialTheme() в hooks/useTheme.ts —
 * keep them in sync.
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
