/**
 * Переключение темы между «Бумага» и «Лофт».
 * Состояние сохраняется в localStorage и восстанавливается inline-скриптом
 * в <head>, чтобы не было «вспышки» неправильной темы при загрузке.
 */
(function () {
    'use strict';

    const STORAGE_KEY = 'kairos.theme';
    const THEMES = ['paper', 'loft'];
    const LABELS = {
        // Подпись на кнопке = название следующей темы (на которую переключимся)
        paper: 'Лофт',
        loft:  'Бумага'
    };

    const html = document.documentElement;
    const toggle = document.getElementById('themeToggle');
    const label = document.getElementById('themeToggleLabel');

    if (!toggle || !label) {
        return;
    }

    function getCurrentTheme() {
        const t = html.getAttribute('data-theme');
        return THEMES.indexOf(t) !== -1 ? t : 'paper';
    }

    function updateLabel() {
        label.textContent = LABELS[getCurrentTheme()];
    }

    function setTheme(theme) {
        if (THEMES.indexOf(theme) === -1) return;
        html.setAttribute('data-theme', theme);
        try { localStorage.setItem(STORAGE_KEY, theme); } catch (e) {}
        updateLabel();
    }

    updateLabel();

    toggle.addEventListener('click', function () {
        const current = getCurrentTheme();
        const next = current === 'paper' ? 'loft' : 'paper';
        setTheme(next);
    });
})();
