/**
 * Скрипт профиля: подсветка активной секции в side-nav при скролле.
 * Аналогично settings.js, но без логики настроек.
 */
(function () {
    'use strict';

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
        const offset = 80;
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
