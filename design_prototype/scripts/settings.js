/**
 * Логика страницы настроек:
 * 1. Применение темы при клике на превью
 * 2. Подсветка текущей темы
 * 3. Скролл-связь side-nav и секций (active по скроллу)
 * 4. Сегментные контролы (размер шрифта, высота строк)
 */
(function () {
    'use strict';

    const STORAGE_KEY = 'kairos.theme';
    const html = document.documentElement;

    // ---------- Превью тем (визуальные кнопки выбора) ----------
    const previews = document.querySelectorAll('[data-theme-choice]');

    function syncPreviewActive() {
        const current = html.getAttribute('data-theme') || 'paper';
        previews.forEach(function (p) {
            const choice = p.getAttribute('data-theme-choice');
            p.classList.toggle('is-active', choice === current);
        });
    }

    previews.forEach(function (p) {
        p.addEventListener('click', function () {
            const choice = p.getAttribute('data-theme-choice');
            if (!choice) return;
            html.setAttribute('data-theme', choice);
            try { localStorage.setItem(STORAGE_KEY, choice); } catch (e) {}
            syncPreviewActive();
        });
    });

    syncPreviewActive();

    // ---------- Сегментные контролы ----------
    document.querySelectorAll('.segmented').forEach(function (group) {
        const items = group.querySelectorAll('.segmented__item');
        items.forEach(function (item) {
            item.addEventListener('click', function () {
                items.forEach(function (i) {
                    i.classList.remove('is-active');
                    i.setAttribute('aria-checked', 'false');
                });
                item.classList.add('is-active');
                item.setAttribute('aria-checked', 'true');
            });
        });
    });

    // ---------- Подсветка текущего раздела в side-nav при скролле ----------
    const sideLinks = document.querySelectorAll('.side-nav__item[href^="#"]');
    const sections = Array.from(sideLinks)
        .map(function (l) {
            const id = l.getAttribute('href').slice(1);
            return { link: l, el: document.getElementById(id) };
        })
        .filter(function (x) { return x.el; });

    const content = document.querySelector('.page__content');
    if (!content || sections.length === 0) return;

    function setActive(linkToActivate) {
        sideLinks.forEach(function (l) { l.classList.remove('is-active'); });
        if (linkToActivate) linkToActivate.classList.add('is-active');
    }

    function onScroll() {
        const scrollTop = content.scrollTop;
        const offset = 80; // компенсируем верхний отступ контента
        let active = sections[0];
        for (let i = 0; i < sections.length; i++) {
            const top = sections[i].el.offsetTop - offset;
            if (scrollTop >= top) {
                active = sections[i];
            } else {
                break;
            }
        }
        setActive(active.link);
    }

    content.addEventListener('scroll', onScroll, { passive: true });

    // Плавный скролл к секции при клике на side-nav
    sideLinks.forEach(function (link) {
        link.addEventListener('click', function (e) {
            const href = link.getAttribute('href');
            if (!href || !href.startsWith('#')) return;
            const target = document.getElementById(href.slice(1));
            if (!target) return;
            e.preventDefault();
            content.scrollTo({
                top: target.offsetTop - 32,
                behavior: 'smooth'
            });
        });
    });
})();
