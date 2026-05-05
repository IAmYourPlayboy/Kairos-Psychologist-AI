/**
 * Сворачивание/разворачивание сайдбара по клику на бургер.
 * Состояние сохраняется в localStorage, чтобы пользователь не настраивал заново.
 */
(function () {
    'use strict';

    const STORAGE_KEY = 'kairos.sidebar.collapsed';

    const appShell = document.querySelector('.app-shell');
    const burger = document.getElementById('burgerToggle');

    if (!appShell || !burger) {
        return;
    }

    // Восстанавливаем сохранённое состояние
    const wasCollapsed = localStorage.getItem(STORAGE_KEY) === 'true';
    if (wasCollapsed) {
        appShell.classList.add('is-sidebar-collapsed');
        burger.setAttribute('aria-expanded', 'false');
        burger.setAttribute('aria-label', 'Развернуть меню');
        burger.setAttribute('title', 'Развернуть меню');
    }

    burger.addEventListener('click', function () {
        const isCollapsed = appShell.classList.toggle('is-sidebar-collapsed');

        burger.setAttribute('aria-expanded', isCollapsed ? 'false' : 'true');
        burger.setAttribute(
            'aria-label',
            isCollapsed ? 'Развернуть меню' : 'Свернуть меню'
        );
        burger.setAttribute(
            'title',
            isCollapsed ? 'Развернуть меню' : 'Свернуть меню'
        );

        localStorage.setItem(STORAGE_KEY, isCollapsed ? 'true' : 'false');
    });
})();
