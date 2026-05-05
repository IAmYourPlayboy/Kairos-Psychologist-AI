/**
 * Автоувеличение textarea по высоте контента + отправка по Enter (Shift+Enter — перенос).
 */
(function () {
    'use strict';

    const form = document.getElementById('chatForm');
    if (!form) return;

    const textarea = form.querySelector('.chat__textarea');
    const sendBtn = form.querySelector('.chat__send');

    if (!textarea || !sendBtn) return;

    // Изначально — кнопка неактивна (нечего отправлять)
    function updateSendState() {
        const hasContent = textarea.value.trim().length > 0;
        sendBtn.disabled = !hasContent;
    }
    updateSendState();

    // Авторесайз
    function autoResize() {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }

    textarea.addEventListener('input', function () {
        autoResize();
        updateSendState();
    });

    // Enter — отправка, Shift+Enter — перенос строки
    textarea.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (textarea.value.trim().length > 0) {
                form.requestSubmit();
            }
        }
    });

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        const text = textarea.value.trim();
        if (!text) return;

        // Прототип: просто очищаем поле и логируем (бекенд подключится в Блоке 5)
        console.log('[prototype] Отправлено:', text);
        textarea.value = '';
        autoResize();
        updateSendState();
    });
})();
