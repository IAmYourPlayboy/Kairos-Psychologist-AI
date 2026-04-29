# AI-ПСИХОЛОГ (KAIROS): ЧЕКЛИСТ ПРОГРЕССА

> **Версия**: 2.1 | **Дата**: Апрель 2026 (Сессия 16)
> **Назначение**: Отслеживание выполнения блоков из CLAUDE.md

---

## Легенда

- ⬜ Не начато
- 🔄 В процессе (активно работаем)
- ½ **Код есть, но не протестирован / не подключён к боевой среде**
- ✅ Завершено и проверено (acceptance criteria выполнены, тесты проходят)
- ⏸️ Заблокировано (ждёт другой блок)
- ⚠️ Проблема (требует внимания)

> **Важно**: статус ½ означает «фундамент написан, но без подключения к БД/LLM/тестов нельзя считать блок завершённым». При появлении реальной интеграции — переводим в ✅.

---

## ФУНДАМЕНТ (Месяц 1, бюджет: 0-1 000₽)

### ½ Блок 1 — Бекенд: FastAPI каркас
**Статус**: Код есть, не запускался в этой сессии
**Зависимости**: Нет
**Acceptance Criteria**:
- [x] Создана структура проекта согласно CLAUDE.md
- [x] app/main.py с FastAPI app, CORS, middleware (RequestIDMiddleware)
- [x] app/config.py с Pydantic Settings
- [x] app/api/router.py с главным роутером
- [x] app/api/health.py с GET /api/health
- [ ] **Проверка**: `curl http://localhost:8001/api/health` → `{"status": "ok"}` (нужно запустить и убедиться)
- [x] Весь код с русскими комментариями
- [x] Type hints везде

**Что осталось**:
- Запустить `uvicorn app.main:app --reload --port 8001` и проверить `/api/health`
- Перевести статус в ✅ после успешной проверки

---

### ½ Блок 1.5 — .env и secrets management
**Статус**: Базовая часть есть
**Зависимости**: Блок 1
**Acceptance Criteria**:
- [x] `.env.example` создан с шаблоном переменных
- [x] `.env` существует (с дефолтными значениями)
- [x] `.gitignore` в корне игнорирует `.env` (Сессия 16)
- [x] README.md содержит инструкцию по настройке `.env`
- [x] Все секреты (LLM_API_KEY, JWT_SECRET, DATABASE_URL, etc.) в `.env`
- [ ] **Что осталось**: добавить валидацию обязательных переменных в config.py (raise если LLM_API_KEY = "change-me")
- [ ] Понятная ошибка при запуске без правильно заполненного `.env`

---

### ½ Блок 2 — Бекенд: LLM-абстракция
**Статус**: Код есть, не подключён к реальному API
**Зависимости**: Блок 1
**Acceptance Criteria**:
- [x] `app/core/llm/base.py` с BaseLLMProvider (ABC)
- [x] `app/core/llm/openai_compat.py` с OpenAICompatProvider
- [x] `app/core/llm/factory.py` с get_provider()
- [x] `.env` с LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
- [x] `tests/test_llm.py` существует (нужно запустить)
- [ ] **Реальный тест**: `python -c "from app.core.llm.factory import get_provider; ..."` → ответ от LLM
- [ ] Подключено к Yandex Cloud AI Studio API (нужен Блок 2.5)
- [ ] (Опционально) работа с локальным vLLM

**Что осталось**:
- Получить реальный API-ключ Yandex Cloud (Блок 2.5)
- Запустить test_llm.py

---

### ⬜ Блок 2.5 — Подключение Yandex Cloud AI Studio
**Статус**: Не начато  
**Зависимости**: Блок 2  
**Acceptance Criteria**:
- [ ] Зарегистрирован в Yandex Cloud
- [ ] Получен стартовый грант (4 000₽)
- [ ] API-ключ создан для AI Studio
- [ ] LLM_BASE_URL и LLM_API_KEY указаны в .env
- [ ] Тест: генерация через API работает → ответ от Qwen3-14B

**Подзадачи**:
1. Зарегистрироваться в Yandex Cloud
2. Получить стартовый грант
3. Создать API-ключ для AI Studio
4. Обновить .env с ключами
5. Протестировать генерацию через API

**Примечание**: Можно сделать сразу после Блока 2 для тестирования LLM.

---

### ½ Блок 3 — Бекенд: терапевтические промпты
**Статус**: Код есть, тесты нужно прогнать
**Зависимости**: Нет (можно параллельно с Блоком 1-2)
**Acceptance Criteria**:
- [x] `app/core/prompts/base.py` с базовым системным промптом (PROMPT + FORBIDDEN_PHRASES)
- [x] `app/core/prompts/branch_a.py` с SIX C's (мобилизация)
- [x] `app/core/prompts/branch_b.py` с ВОЗ PFA (стабилизация)
- [x] `app/core/prompts/crisis.py` с кризисным промптом
- [x] `app/core/prompts/builder.py` с build_system_prompt()
- [x] `app/core/prompts/forbidden_phrases.py` — словарь запрещённых фраз
- [x] `app/core/prompts/human_style.py` — «живой» стиль (бонус, не было в плане)
- [x] `tests/test_prompts.py` существует
- [ ] **Реально запустить тесты**: проверить что `build_system_prompt("A", "normal")` содержит "МОБИЛИЗАЦИЯ" и не содержит запрещённых фраз

**Что осталось**:
- Запустить `pytest tests/test_prompts.py -v`

---

### ½ Блок 4 — Бекенд: кризисная детекция
**Статус**: Код есть, тесты нужно прогнать
**Зависимости**: Нет
**Acceptance Criteria**:
- [x] `app/core/crisis/detector.py` с `assess_crisis_level()`
- [x] `app/core/crisis/keywords.py` со словарями (IMMEDIATE_KEYWORDS, HIGH_KEYWORDS, ELEVATED_KEYWORDS)
- [x] `app/core/crisis/contacts.py` с кризисными контактами по возрастам
- [x] 3 уровня: immediate, high, elevated
- [x] `tests/test_crisis.py` существует
- [ ] **Реально запустить тесты**: проверить что `assess_crisis_level("хочу умереть")` → `"immediate"`, и т.д.

**Что осталось**:
- Запустить `pytest tests/test_crisis.py -v`

---

### ⬜ Блок 5 — Бекенд: эндпоинт /api/chat ⭐ **ПРИОРИТЕТ #1**
**Статус**: Не начато (главный gap)
**Зависимости**: Блоки 2, 3, 4 (все ½ готовы)
**Acceptance Criteria**:
- [ ] `app/api/chat.py` с POST `/api/chat`
- [ ] Принимает `{message, session_id, age_group?}`
- [ ] Возвращает `{reply, crisis_level, contacts, branch}`
- [ ] Поток: crisis detection → prompt builder → LLM → response
- [ ] Интеграция с `therapy_router.py` (выбор техники)
- [ ] Тест: `POST /api/chat {"message": "мне плохо"}` → ответ по протоколу
- [ ] Тест: `POST /api/chat {"message": "хочу умереть"}` → crisis_level="immediate" + contacts
- [ ] Обработка ошибок LLM (timeout, rate limit, 5xx)

**Подзадачи**:
1. Создать `app/api/chat.py`
2. Интегрировать crisis detector
3. Интегрировать prompt builder + therapy_router
4. Интегрировать LLM provider
5. Добавить обработку ошибок (graceful degradation если LLM недоступен)
6. Написать интеграционные тесты `tests/test_chat.py`

---

### ⬜ Блок 5.5 — API endpoint /api/feedback
**Статус**: Не начато  
**Зависимости**: Блоки 5, 6a  
**Acceptance Criteria**:
- [ ] api/feedback.py с POST /api/feedback
- [ ] Принимает {session_id, message_id, event_type}
- [ ] event_type: "felt_better", "no_change", "thumbs_up", "thumbs_down", "crisis_escalated", "session_timeout"
- [ ] Записывает в таблицу feedback_events
- [ ] Тест: POST /api/feedback → запись в БД

**Подзадачи**:
1. Создать api/feedback.py
2. Добавить роутер в api/router.py
3. Написать тесты

---

### ⬜ Блок 6a — Бекенд: модели данных + БД + Alembic
**Статус**: Не начато  
**Зависимости**: Блок 1  
**Acceptance Criteria**:
- [ ] app/data/models.py с таблицами (users, chat_sessions, messages, feedback_events, subscriptions)
- [ ] app/data/database.py с AsyncSession, engine, get_db()
- [ ] Alembic настроен для миграций
- [ ] Первая миграция создана (создание таблиц)
- [ ] Тест: миграция применяется → таблицы созданы

**Подзадачи**:
1. Создать app/data/models.py с SQLAlchemy моделями
2. Создать app/data/database.py с подключением
3. Настроить Alembic (alembic.ini, env.py)
4. Создать первую миграцию: `alembic revision --autogenerate -m "Initial tables"`
5. Применить миграцию: `alembic upgrade head`
6. Написать тесты для моделей

---

### ⬜ Блок 6b — Бекенд: data logger + pipeline
**Статус**: Не начато  
**Зависимости**: Блоки 5, 6a  
**Acceptance Criteria**:
- [ ] app/data/logger.py с логированием каждого сообщения
- [ ] Каждое сообщение из /api/chat записывается в messages
- [ ] Каждая сессия записывается в chat_sessions
- [ ] Тест: POST /api/chat → SELECT * FROM messages → запись есть

**Подзадачи**:
1. Создать app/data/logger.py
2. Интегрировать с api/chat.py (запись после каждого ответа)
3. Записывать метаданные (crisis_level, emotion, distress_score, response_time_ms, tokens)
4. Написать тесты

---

### ⬜ Блок 6c — Бекенд: анонимизация + research export
**Статус**: Не начато  
**Зависимости**: Блок 6b  
**Acceptance Criteria**:
- [ ] app/data/anonymizer.py с многоуровневой анонимизацией:
  1. Regex-замена ПДн (имена, телефоны, email, адреса → заглушки)
  2. География → только регион (Москва, не Тверская ул. 15)
  3. Возраст → группы (до 18 / 18-25 / 25-35 / 35-50 / 50+)
  4. K-анонимность (k≥5): удаление записей с уникальными комбинациями
  5. Лог удалённых полей (для аудита и воспроизводимости исследований)
- [ ] app/data/research_export.py — экспорт обезличенного датасета для LoRA/исследований
- [ ] Тест: после POST /api/chat → SELECT * FROM messages → ПДн удалены
- [ ] Тест: K-анонимность работает (k≥5)

**Подзадачи**:
1. Создать app/data/anonymizer.py с 5 уровнями анонимизации
2. Интегрировать с logger.py (анонимизация перед записью)
3. Создать app/data/research_export.py
4. Написать тесты для анонимизации
5. Написать тесты для K-анонимности

---

### ⬜ Блок 6d — Бекенд: middleware (request_id, CORS, error handling)
**Статус**: Не начато  
**Зависимости**: Блок 1  
**Acceptance Criteria**:
- [ ] app/middleware/request_id.py — X-Request-ID для трейсинга
- [ ] CORS настроен в main.py (разрешены только нужные origins)
- [ ] Security headers настроены (X-Content-Type-Options, X-Frame-Options, etc.)
- [ ] Глобальный error handler для 500 ошибок
- [ ] Тест: каждый запрос имеет X-Request-ID в логах

**Подзадачи**:
1. Создать app/middleware/request_id.py
2. Настроить CORS в main.py
3. Добавить security headers
4. Создать глобальный error handler
5. Написать тесты

---

### ⬜ Блок 7 — Фронтенд: Next.js каркас ⭐ **ПРИОРИТЕТ #3**
**Статус**: Не начато (есть 2 готовых компонента, но нет проекта Next.js)
**Зависимости**: Нет (можно параллельно с бекендом)
**⚠️ Важно**: Сейчас в `frontend/components/Chat/` уже есть `MessageBubble.tsx` и `HumanTypingEffect.tsx` — их нужно **сохранить** при инициализации проекта.

**Acceptance Criteria**:
- [ ] `npx create-next-app@latest` запущен с `--ts --tailwind --app --src-dir=false`
- [ ] Сохранены существующие `MessageBubble.tsx` + `HumanTypingEffect.tsx`
- [ ] `package.json` создан с зависимостями
- [ ] Шрифт Golos Text подключён
- [ ] Палитра тёплых тонов настроена в tailwind.config.js
- [ ] `app/layout.tsx` с метаданными
- [ ] `app/globals.css` с Tailwind
- [ ] `next.config.js` с rewrites `/api/` → `http://localhost:8001`
- [ ] Тест: `npm run dev` → страница открывается на `http://localhost:3000`

**Подзадачи**:
1. Сохранить `frontend/components/Chat/*.tsx` во временную папку
2. Запустить `npx create-next-app@latest frontend` (или в `frontend-new` и потом перенести)
3. Настроить TypeScript strict mode
4. Настроить Tailwind CSS
5. Подключить шрифт Golos Text (через next/font/google)
6. Создать палитру цветов
7. Настроить `next.config.js` для проксирования API
8. Вернуть существующие компоненты в `components/Chat/`

---

### ¼ Блок 8 — Фронтенд: чат-интерфейс
**Статус**: 2 из 5 компонентов готовы
**Зависимости**: Блок 7
**Acceptance Criteria**:
- [ ] components/Chat/ChatContainer.tsx
- [x] components/Chat/MessageBubble.tsx ✓
- [x] components/Chat/HumanTypingEffect.tsx ✓ (бонус — «живая» печать)
- [ ] components/Chat/TypingIndicator.tsx
- [ ] components/Chat/QuickReplies.tsx
- [ ] components/Chat/InputArea.tsx
- [ ] hooks/useChat.ts с логикой чата
- [ ] Тест: набрал «мне плохо» → увидел ответ бота
- [ ] Авто-скролл к последнему сообщению

**Подзадачи**:
1. После Блока 7 (npm install, etc.):
2. Создать оставшиеся компоненты: ChatContainer, TypingIndicator, QuickReplies, InputArea
3. Создать hooks/useChat.ts
4. Интегрировать с API /chat (Блок 5 должен быть готов)
5. Добавить авто-скролл
6. Стилизовать пузыри (MessageBubble уже стилизован — Tailwind)

---

### ⬜ Блок 9 — Фронтенд: кризисный блок
**Статус**: Не начато  
**Зависимости**: Блок 8  
**Acceptance Criteria**:
- [ ] components/Crisis/SOSButton.tsx в шапке (всегда видна)
- [ ] components/Crisis/CrisisPanel.tsx с номерами
- [ ] components/Crisis/CrisisInlineCard.tsx в чате
- [ ] SOS-кнопка пульсирует при crisis_level > normal
- [ ] Панель с номерами (112, МЧС, телефоны доверия)
- [ ] Тест: при ответе с crisis_contacts → карточка с номерами в чате

**Подзадачи**:
1. Создать SOSButton.tsx
2. Создать CrisisPanel.tsx
3. Создать CrisisInlineCard.tsx
4. Добавить анимацию пульсации
5. Интегрировать с crisis_level из API

---

### ⬜ Блок 10 — Фронтенд: локальное хранилище (Dexie.js)
**Статус**: Не начато  
**Зависимости**: Блок 8  
**Acceptance Criteria**:
- [ ] lib/db.ts с Dexie БД (sessions, messages, syncQueue)
- [ ] hooks/useSession.ts с guestId в localStorage
- [ ] Каждое сообщение сохраняется в IndexedDB + отправляется на сервер
- [ ] При возврате: «С возвращением. Хочешь продолжить?»
- [ ] Тест: закрыл вкладку → открыл → чат на месте

**Подзадачи**:
1. Установить Dexie.js
2. Создать lib/db.ts со схемой
3. Создать hooks/useSession.ts
4. Интегрировать с useChat.ts
5. Добавить логику возврата

---

### ⬜ Блок 11 — Фронтенд: обратная связь
**Статус**: Не начато  
**Зависимости**: Блоки 8, 5.5  
**Acceptance Criteria**:
- [ ] components/Feedback/SessionFeedback.tsx
- [ ] «Стало легче?» [Да] [Нет] [Не уверен]
- [ ] Показывается после завершения протокола
- [ ] Записывается в feedback_events на сервере
- [ ] Тест: нажал «Да» → POST /api/feedback → запись в БД

**Подзадачи**:
1. Создать SessionFeedback.tsx
2. Интегрировать с useChat.ts
3. Добавить логику показа после протокола

---

## ИНТЕГРАЦИЯ (Месяц 2, бюджет: ~2 000₽)

### ⬜ Блок 12 — Бекенд: Aniemore (NLP)
**Статус**: Не начато  
**Зависимости**: Блок 5  
**Acceptance Criteria**:
- [ ] app/core/nlp/emotion.py с EmotionAnalyzer
- [ ] app/core/nlp/markers.py с лингвистическими маркерами
- [ ] app/core/nlp/pipeline.py с NLPPipeline
- [ ] pip install aniemore выполнен
- [ ] Модель rubert-tiny2 загружается при старте
- [ ] NLPContext передаётся в build_system_prompt()
- [ ] Тест: `analyze("мне страшно")` → emotion="страх", distress_score=0.6

**Подзадачи**:
1. Изучить skills/nlp-emotion-analysis.md
2. Установить Aniemore
3. Создать app/core/nlp/emotion.py
4. Создать app/core/nlp/markers.py
5. Создать app/core/nlp/pipeline.py
6. Интегрировать с /api/chat
7. Написать тесты

---

### ⬜ Блок 12.5 — Бекенд: тесты (pytest)
**Статус**: Не начато  
**Зависимости**: Блоки 1-12  
**Acceptance Criteria**:
- [ ] tests/test_crisis.py — тесты кризисной детекции (все 3 уровня)
- [ ] tests/test_prompts.py — тесты промптов (запрещённые фразы, ветвление)
- [ ] tests/test_auth.py — тесты авторизации (register, login, JWT)
- [ ] tests/test_chat.py — интеграционные тесты /api/chat
- [ ] tests/test_sync.py — тесты синхронизации
- [ ] pytest настроен, все тесты проходят

**Подзадачи**:
1. Настроить pytest + pytest-asyncio
2. Создать fixtures для БД и тестовых данных
3. Написать тесты для кризисной детекции
4. Написать тесты для промптов
5. Написать тесты для авторизации
6. Написать интеграционные тесты /api/chat
7. Написать тесты для синхронизации

---

### ⬜ Блок 13 — Бекенд: аутентификация (email + пароль)
**Статус**: Не начато  
**Зависимости**: Блок 6a  
**Acceptance Criteria**:
- [ ] app/core/auth/jwt.py с созданием/валидацией JWT
- [ ] app/core/auth/password.py с хешированием (pwdlib + Argon2)
- [ ] app/core/auth/dependencies.py с get_current_user()
- [ ] app/api/auth.py с POST /register, /login, /refresh, /logout
- [ ] httpOnly cookies настроены
- [ ] Тест: register → login → cookie установлен → /api/chat с cookie → работает

**Подзадачи**:
1. Создать app/core/auth/jwt.py
2. Создать app/core/auth/password.py
3. Создать app/core/auth/dependencies.py
4. Создать app/api/auth.py
5. Настроить httpOnly cookies
6. Написать тесты

---

### ⬜ Блок 14 — Фронтенд: страницы авторизации (email)
**Статус**: Не начато  
**Зависимости**: Блоки 7, 13  
**Acceptance Criteria**:
- [ ] app/auth/login/page.tsx с формой логина
- [ ] app/auth/register/page.tsx с формой регистрации
- [ ] components/Auth/LoginForm.tsx (email + пароль)
- [ ] Мягкое предложение: «Хочешь сохранить историю? Создай аккаунт» (не навязывается)
- [ ] Тест: зарегистрировался → залогинился → перешёл в чат

**Подзадачи**:
1. Создать app/auth/login/page.tsx
2. Создать app/auth/register/page.tsx
3. Создать components/Auth/LoginForm.tsx
4. Добавить мягкое предложение регистрации в чат
5. Стилизовать формы

---

### ⬜ Блок 15 — Синхронизация: клиент → сервер
**Статус**: Не начато  
**Зависимости**: Блоки 10, 13  
**Acceptance Criteria**:
- [ ] api/sync.py с POST /api/sync (batch upsert)
- [ ] api/sync.py с GET /api/pull (since timestamp)
- [ ] api/sync.py с POST /api/sync/migrate (привязка guest чатов к аккаунту)
- [ ] lib/sync.ts — sync engine (push pending → pull new → update Dexie)
- [ ] hooks/useSync.ts — автоматический sync при онлайне, queue при офлайне
- [ ] Тест: зарегался → старые чаты привязались к аккаунту

**Подзадачи**:
1. Создать api/sync.py с эндпоинтами
2. Создать lib/sync.ts с sync engine
3. Создать hooks/useSync.ts
4. Интегрировать с useChat.ts
5. Написать тесты миграции guest → user

---

### ⬜ Блок 16 — Фронтенд: профиль + история чатов
**Статус**: Не начато  
**Зависимости**: Блоки 14, 15  
**Acceptance Criteria**:
- [ ] app/profile/page.tsx с профилем пользователя
- [ ] Список прошлых сессий (дата, длительность, ветка, outcome)
- [ ] Статус подписки (если есть)
- [ ] Тест: открыл профиль → вижу историю всех чатов

**Подзадачи**:
1. Создать app/profile/page.tsx
2. Создать компонент списка сессий
3. Интегрировать с API /api/pull
4. Добавить отображение статуса подписки

---

### ⬜ Блок 16.5 — Фронтенд: тесты (Playwright)
**Статус**: Не начато  
**Зависимости**: Блоки 7-16  
**Acceptance Criteria**:
- [ ] Playwright настроен
- [ ] tests/e2e/chat.spec.ts — тесты чата
- [ ] tests/e2e/auth.spec.ts — тесты авторизации
- [ ] tests/e2e/crisis.spec.ts — тесты кризисного блока
- [ ] Все тесты проходят

**Подзадачи**:
1. Установить Playwright
2. Настроить playwright.config.ts
3. Написать тесты для чата
4. Написать тесты для авторизации
5. Написать тесты для кризисного блока

---

## DEPLOY (Месяц 2-3, бюджет: ~2 000-3 000₽)

### ⬜ Блок 17 — Покупка домена
**Статус**: Не начато  
**Зависимости**: Нет  
**Acceptance Criteria**:
- [ ] Домен .ru куплен на REG.RU (~129₽/год)
- [ ] DNS настроен: A-запись → IP VPS (или через Cloudflare)
- [ ] Тест: `ping aipsycholog.ru` → отвечает

**Подзадачи**:
1. Зарегистрироваться на REG.RU
2. Купить домен .ru
3. Настроить DNS (A-запись)

---

### ⬜ Блок 18 — Покупка VPS
**Статус**: Не начато  
**Зависимости**: Нет (можно сделать раньше для удалённой БД)  
**Acceptance Criteria**:
- [ ] VPS куплен на Timeweb Cloud (2 vCPU / 4 ГБ RAM / 50 ГБ NVMe, Москва)
- [ ] Ubuntu 22.04 установлен
- [ ] Docker + Docker Compose установлены
- [ ] PostgreSQL + Redis подняты в Docker на VPS
- [ ] Тест: `ssh root@<ip>` → `docker --version` → работает

**Подзадачи**:
1. Зарегистрироваться на Timeweb Cloud
2. Купить VPS (2 vCPU / 4 ГБ RAM, Москва)
3. Установить Docker + Docker Compose
4. Поднять PostgreSQL + Redis в Docker
5. Настроить удалённый доступ к БД

**Примечание**: Можно сделать раньше (до Блока 1) для использования как удалённой БД при разработке.

---

### ⬜ Блок 19 — Docker Compose (production)
**Статус**: Не начато  
**Зависимости**: Блок 18  
**Acceptance Criteria**:
- [ ] docker-compose.yml с Nginx + Next.js + FastAPI + PostgreSQL + Redis
- [ ] nginx.conf: / → frontend:3000, /api/ → backend:8001
- [ ] .env.production с всеми ключами (LLM, БД, Redis, JWT_SECRET, YOOKASSA)
- [ ] Тест: `docker compose up -d` → сайт открывается по IP

**Подзадачи**:
1. Создать docker-compose.yml
2. Создать nginx.conf
3. Создать .env.production
4. Создать Dockerfile для бекенда
5. Создать Dockerfile для фронтенда
6. Протестировать локально
7. Задеплоить на VPS

---

### ⬜ Блок 20 — SSL + Cloudflare
**Статус**: Не начато  
**Зависимости**: Блоки 17, 19  
**Acceptance Criteria**:
- [ ] Cloudflare: домен добавлен, прокси включён (оранжевое облако)
- [ ] SSL сертификат настроен (Let's Encrypt или Cloudflare)
- [ ] Тест: `https://aipsycholog.ru` → зелёный замок

**Подзадачи**:
1. Добавить домен в Cloudflare
2. Настроить DNS через Cloudflare
3. Включить прокси (оранжевое облако)
4. Настроить SSL (Let's Encrypt через certbot или Cloudflare SSL)

---

### ⬜ Блок 21 — CI/CD (GitHub Actions)
**Статус**: Не начато  
**Зависимости**: Блоки 12.5, 19  
**Acceptance Criteria**:
- [ ] .github/workflows/deploy.yml создан
- [ ] Push в main → pytest → docker build → ssh → docker compose pull → up -d
- [ ] Тест: `git push` → через 3 минуты → новая версия на сервере

**Подзадачи**:
1. Создать .github/workflows/deploy.yml
2. Настроить SSH-ключи для деплоя
3. Добавить секреты в GitHub (SSH_KEY, HOST, etc.)
4. Протестировать деплой

---

## ПЛАТЕЖИ (Месяц 3-4, бюджет: время на юридику)

### ⬜ Блок 22 — Регистрация самозанятого
**Статус**: Не начато  
**Зависимости**: Нет  
**Тип**: Организационное (не код)  
**Acceptance Criteria**:
- [ ] Зарегистрирован как самозанятый через приложение «Мой налог»
- [ ] Налог 4% с физлиц настроен
- [ ] Лимит 2.4 млн₽/год понятен

**Подзадачи**:
1. Скачать приложение «Мой налог»
2. Пройти регистрацию
3. Изучить правила самозанятости

---

### ⬜ Блок 23 — Подключение ЮKassa
**Статус**: Не начато  
**Зависимости**: Блок 22  
**Acceptance Criteria**:
- [ ] Зарегистрирован на yookassa.ru как самозанятый
- [ ] «Чеки от ЮKassa» включены (автоформирование чеков для ФНС)
- [ ] shopId + secretKey получены
- [ ] Webhook URL настроен
- [ ] Автоплатежи активированы (запрос у менеджера)
- [ ] Тест: sandbox-платёж → webhook → запись в subscriptions

**Подзадачи**:
1. Зарегистрироваться на yookassa.ru
2. Включить «Чеки от ЮKassa»
3. Получить shopId + secretKey
4. Настроить webhook URL
5. Запросить активацию автоплатежей у менеджера
6. Протестировать в sandbox

---

### ⬜ Блок 24 — Бекенд: платёжная логика
**Статус**: Не начато  
**Зависимости**: Блоки 6a, 23  
**Acceptance Criteria**:
- [ ] app/core/payments/yookassa_client.py — обёртка над yookassa SDK
- [ ] app/core/payments/subscription.py — логика подписок (создание, продление, отмена)
- [ ] app/core/payments/webhooks.py — обработка ЮKassa webhooks
- [ ] api/subscription.py — POST /api/subscription/create, POST /api/subscription/webhook
- [ ] Cron: ежедневная проверка подписок → автосписание → grace period → деградация
- [ ] Тест: оплатил → подписка active → через месяц → автосписание

**Подзадачи**:
1. Установить yookassa SDK
2. Создать app/core/payments/yookassa_client.py
3. Создать app/core/payments/subscription.py
4. Создать app/core/payments/webhooks.py
5. Создать api/subscription.py
6. Настроить cron для проверки подписок
7. Написать тесты

---

### ⬜ Блок 25 — Фронтенд: тарифы и оплата
**Статус**: Не начато  
**Зависимости**: Блоки 7, 24  
**Acceptance Criteria**:
- [ ] components/Subscription/PricingCards.tsx — 3 карточки (бесплатно / поддержка / двойник)
- [ ] components/Subscription/PaymentWidget.tsx — встраивание ЮKassa Checkout Widget
- [ ] Страница отписки (обязательна для ЮKassa)
- [ ] Тест: выбрал тариф → оплатил → подписка отображается в профиле

**Подзадачи**:
1. Создать components/Subscription/PricingCards.tsx
2. Создать components/Subscription/PaymentWidget.tsx
3. Создать страницу отписки
4. Интегрировать с API /api/subscription/create
5. Стилизовать карточки тарифов

---

### ⬜ Блок 26 — Юридические страницы
**Статус**: Не начато  
**Зависимости**: Блок 7  
**Acceptance Criteria**:
- [ ] /legal/privacy — Политика конфиденциальности (ФЗ-152)
- [ ] /legal/terms — Пользовательское соглашение
- [ ] /legal/offer — Публичная оферта
- [ ] /legal/consent — Информированное согласие

**Подзадачи**:
1. Создать app/legal/privacy/page.tsx
2. Создать app/legal/terms/page.tsx
3. Создать app/legal/offer/page.tsx
4. Создать app/legal/consent/page.tsx
5. Написать тексты (можно с помощью юриста)

---

### ⬜ Блок 27 — Чекбоксы согласий + интеграция
**Статус**: Не начато  
**Зависимости**: Блоки 14, 26  
**Acceptance Criteria**:
- [ ] Чекбоксы при регистрации (3 штуки)
- [ ] Регистрация невозможна без всех трёх чекбоксов
- [ ] Тест: попытка зарегистрироваться без чекбоксов → ошибка

**Подзадачи**:
1. Добавить чекбоксы в форму регистрации
2. Добавить валидацию на фронтенде
3. Добавить валидацию на бекенде (POST /register)
4. Записывать согласия в БД (таблица users)

---

## ПОЛИРОВКА (Месяц 3-4)

### ⬜ Блок 28 — Таймер дыхания
**Статус**: Не начато  
**Зависимости**: Блок 8  
**Acceptance Criteria**:
- [ ] components/Chat/BreathingTimer.tsx — визуальный круг
- [ ] Расширяется на вдохе (4 сек), пауза (4 сек), сжимается на выдохе (6 сек)
- [ ] Встраивается в чат когда бот предлагает дыхательное упражнение
- [ ] Тест: бот предложил дыхание → таймер появился → работает

**Подзадачи**:
1. Создать components/Chat/BreathingTimer.tsx
2. Добавить анимацию круга (CSS или Framer Motion)
3. Интегрировать с чатом

---

### ⬜ Блок 29 — Обработка молчания и возврата
**Статус**: Не начато  
**Зависимости**: Блоки 8, 10  
**Acceptance Criteria**:
- [ ] Фронтенд: при возврате с тем же session_id → показать "С возвращением. Хочешь продолжить?"
- [ ] Тест: закрыл вкладку → открыл через час → увидел приветствие

**Подзадачи**:
1. Добавить логику в useSession.ts
2. Показывать приветствие при возврате
3. Предложить продолжить или начать новую сессию

---

### ⬜ Блок 30 — Аналитический dashboard (/admin)
**Статус**: Не начато  
**Зависимости**: Блок 6b  
**Acceptance Criteria**:
- [ ] api/admin.py — защищённый паролем
- [ ] Метрики: сессии, кризисы, feedback, ветки A/B, время, токены, темы
- [ ] Тест: открыл /admin → ввёл пароль → увидел метрики

**Подзадачи**:
1. Создать api/admin.py с защитой паролем
2. Создать SQL-запросы для метрик
3. Создать простой HTML-дашборд

---

### ⬜ Блок 31 — Rate limiting + Prompt injection protection
**Статус**: Не начато  
**Зависимости**: Блоки 1, 5  
**Acceptance Criteria**:
- [ ] middleware/rate_limit.py — 30 сообщений/мин на сессию, 100 сессий/час на IP
- [ ] В system prompt: блок «ЗАЩИТА» от injection
- [ ] Тесты: 20 adversarial промптов → все обработаны безопасно
- [ ] Тест: превышение лимита → 429 Too Many Requests

**Подзадачи**:
1. Создать middleware/rate_limit.py (Redis-backed)
2. Добавить блок защиты в system prompt
3. Написать adversarial тесты
4. Интегрировать middleware в FastAPI

---

### ⬜ Блок 32 — Стресс-тестирование
**Статус**: Не начато  
**Зависимости**: Блоки 19, 21  
**Acceptance Criteria**:
- [ ] locust или k6 настроен
- [ ] Тест: 50 одновременных пользователей
- [ ] Время ответа < 5 сек
- [ ] Сервер не падает

**Подзадачи**:
1. Установить locust или k6
2. Написать сценарий нагрузки
3. Запустить тест на VPS
4. Оптимизировать узкие места

---

### ⬜ Блок 33 — Дисклеймеры в интерфейсе
**Статус**: Не начато  
**Зависимости**: Блоки 8, 9  
**Acceptance Criteria**:
- [ ] Слой 1: модальное окно при первом входе
- [ ] Слой 2: inline в чате при кризисе
- [ ] Слой 3: футер на каждой странице
- [ ] Слой 4: уведомление о сборе данных

**Подзадачи**:
1. Создать components/Disclaimer/FirstVisitModal.tsx
2. Создать components/Disclaimer/DataConsentBanner.tsx
3. Создать components/Disclaimer/FooterDisclaimer.tsx
4. Интегрировать в layout.tsx и чат

---

### ⬜ Блок 34 — Бэкапы PostgreSQL
**Статус**: Не начато  
**Зависимости**: Блок 18  
**Acceptance Criteria**:
- [ ] Cron: pg_dump ежедневно → хранение 30 дней
- [ ] Или: Timeweb Cloud автобэкапы включены
- [ ] Тест: бэкап создан → можно восстановить

**Подзадачи**:
1. Настроить cron для pg_dump
2. Настроить ротацию бэкапов
3. Протестировать восстановление

---

### ⬜ Блок 35 — Мониторинг
**Статус**: Не начато  
**Зависимости**: Блоки 19, 17  
**Acceptance Criteria**:
- [ ] Sentry Free: отслеживание ошибок (Python + Next.js)
- [ ] UptimeRobot Free: пинг каждые 5 минут
- [ ] Тест: вызвал ошибку → Sentry поймал

**Подзадачи**:
1. Зарегистрироваться на Sentry
2. Интегрировать Sentry в FastAPI
3. Интегрировать Sentry в Next.js
4. Настроить UptimeRobot

---

### ⬜ Блок 36 — Заявка на грант
**Статус**: Не начато  
**Зависимости**: Блоки 19-20 (работающий сайт)  
**Тип**: Организационное (не код)  
**Acceptance Criteria**:
- [ ] Заявка на Yandex Cloud Boost Start подана (50 000₽ на 6 месяцев)
- [ ] Описание проекта подготовлено
- [ ] Работающий сайт доступен для демонстрации

**Подзадачи**:
1. Изучить требования Yandex Cloud Boost Start
2. Подготовить описание проекта
3. Подать заявку

---

## ПОСЛЕ MVP (Фаза 5-8)

### ⬜ Блок 37 — LoRA fine-tuning
**Статус**: Не начато  
**Зависимости**: Блок 6c  
**Acceptance Criteria**:
- [ ] Экспорт данных через research_export.py
- [ ] Формат JSONL с messages готов
- [ ] LoRA обучение запущено (Yandex Cloud DataSphere или Colab Pro)
- [ ] Новая модель протестирована

**Подзадачи**:
1. Собрать 500+ диалогов с feedback
2. Экспортировать через research_export.py
3. Подготовить JSONL датасет
4. Настроить обучение LoRA
5. Протестировать новую модель

---

### ⬜ Блок 38 — A/B тестирование промптов
**Статус**: Не начато  
**Зависимости**: Блок 37  
**Acceptance Criteria**:
- [ ] 50% пользователей → prompt_v1, 50% → prompt_v2
- [ ] Сравнение: completion_rate, improvement_rate, session_duration
- [ ] Минимум 100 сессий на вариант

**Подзадачи**:
1. Создать систему A/B тестирования
2. Подготовить 2 варианта промптов
3. Запустить тест
4. Проанализировать результаты

---

### ⬜ Блок 39 — ElevenLabs TTS
**Статус**: Не начато  
**Зависимости**: Блок 28  
**Acceptance Criteria**:
- [ ] ElevenLabs API интегрирован
- [ ] TTS для дыхательных упражнений работает
- [ ] Тест: бот предложил упражнение → голос воспроизвёлся

**Подзадачи**:
1. Зарегистрироваться на ElevenLabs
2. Интегрировать API
3. Добавить голосовой режим для упражнений

---

### ⬜ Блок 40 — CBT/DBT/ACT терапевтический режим
**Статус**: Не начато  
**Зависимости**: Блоки 3, 12  
**Acceptance Criteria**:
- [ ] Промпты для CBT/DBT/ACT созданы
- [ ] PHQ-9 / GAD-7 каждые 2 недели
- [ ] Дневник мыслей (CBT)
- [ ] Тест: выбрал CBT → получил соответствующую терапию

**Подзадачи**:
1. Изучить CBT/DBT/ACT протоколы
2. Создать промпты для каждого подхода
3. Добавить скрининг PHQ-9 / GAD-7
4. Создать дневник мыслей

---

### ⬜ Блок 41 — Цифровой двойник
**Статус**: Не начато  
**Зависимости**: Блоки 39, 40  
**Acceptance Criteria**:
- [ ] Анкета для создания профиля двойника
- [ ] ElevenLabs PVC для клонирования голоса
- [ ] Адаптивное угасание (3-12 мес)
- [ ] Тест: создал двойника → общался → угасание началось

**Подзадачи**:
1. Создать анкету профиля
2. Интегрировать ElevenLabs PVC
3. Реализовать механику угасания
4. Добавить переход в терапию после угасания

---

### ⬜ Блок 42 — Мобильное приложение (Capacitor)
**Статус**: Не начато  
**Зависимости**: Блоки 7-16  
**Acceptance Criteria**:
- [ ] Capacitor настроен
- [ ] iOS/Android сборки работают
- [ ] IndexedDB/Dexie работает в WebView
- [ ] Push-уведомления для check-in

**Подзадачи**:
1. Установить Capacitor
2. Настроить iOS проект
3. Настроить Android проект
4. Добавить push-уведомления
5. Протестировать на устройствах

---

### ⬜ Блок 43 — Десктоп (Tauri 2.0)
**Статус**: Не начато  
**Зависимости**: Блоки 7-16  
**Acceptance Criteria**:
- [ ] Tauri 2.0 настроен
- [ ] Windows/macOS/Linux сборки работают
- [ ] Бинарник ~5-10 МБ
- [ ] Оффлайн-кеш для упражнений

**Подзадачи**:
1. Установить Tauri 2.0
2. Настроить Rust бекенд
3. Создать сборки для всех платформ
4. Добавить оффлайн-кеш

---

## ОПЦИОНАЛЬНЫЕ ФИЧИ (после MVP)

### ⬜ Блок 44 — Telegram OAuth
**Статус**: Не начато  
**Зависимости**: Блок 13  
**Acceptance Criteria**:
- [ ] app/core/auth/telegram.py — верификация HMAC-SHA256
- [ ] api/oauth.py — POST /api/auth/telegram
- [ ] Фронтенд: TelegramButton.tsx
- [ ] Тест: вход через Telegram работает

**Подзадачи**:
1. Создать бота в @BotFather
2. Создать app/core/auth/telegram.py
3. Создать TelegramButton.tsx
4. Протестировать авторизацию

---

### ⬜ Блок 45 — VK ID OAuth
**Статус**: Не начато  
**Зависимости**: Блок 13  
**Acceptance Criteria**:
- [ ] app/core/auth/vk.py — обмен кода на токен
- [ ] api/oauth.py — POST /api/auth/vk
- [ ] Фронтенд: VKButton.tsx
- [ ] Тест: вход через VK работает

**Подзадачи**:
1. Зарегистрировать приложение на id.vk.ru
2. Создать app/core/auth/vk.py
3. Создать VKButton.tsx
4. Протестировать авторизацию

---

### ⬜ Блок 46 — SMS-верификация
**Статус**: Не начато  
**Зависимости**: Блок 13  
**Acceptance Criteria**:
- [ ] app/core/auth/sms.py — flash-call через SMSC.ru
- [ ] api/auth.py — POST /api/auth/sms/send, /verify
- [ ] Фронтенд: SMSVerification.tsx
- [ ] Тест: вход через SMS работает

**Подзадачи**:
1. Зарегистрироваться на SMSC.ru
2. Создать app/core/auth/sms.py
3. Создать SMSVerification.tsx
4. Протестировать верификацию

---

## АВТОНОМНЫЕ АГЕНТЫ (после MVP, фундамент уже есть)

> Архитектура полностью описана в `backend/agents/ARCHITECTURE.md` и в CLAUDE.md секция «АГЕНТЫ И БАЗА ЗНАНИЙ».
> Стратегия: полная автоматизация, ~10 000₽/мес из грантов, обработка ~2500 статей/мес.

### ½ Блок 47 — Агенты: базовые классы и инфраструктура
**Статус**: Код есть, не тестировался
**Acceptance Criteria**:
- [x] `agents/shared/base_agent.py` — BaseAgent (ABC) с activate/deactivate/run
- [x] `agents/shared/pubmed_client.py` — PubMed E-utilities API клиент
- [x] `agents/shared/knowledge_base.py` — менеджер эталонных статей
- [x] `agents/__init__.py`, `agents/brain/__init__.py`, `agents/shared/__init__.py`, `agents/culture/__init__.py`
- [ ] `pip install httpx pyyaml` (нужно проверить что в pyproject.toml)
- [ ] Smoke-тест: импорт всех агентов проходит без ошибок

---

### ½ Блок 48 — ResearcherAgent (поиск статей на PubMed)
**Статус**: Код есть, не запускался
**Acceptance Criteria**:
- [x] `agents/brain/researcher_agent.py` с DEFAULT_TOPICS (10 тем)
- [x] Поддержка priority_query от Orchestrator
- [x] Дедупликация по PMID
- [ ] **Реальный тест**: ищет статьи на PubMed по теме «grief bereavement» → возвращает >0 PubMedArticle
- [ ] Опциональное улучшение запроса через LLM

---

### ½ Блок 49 — ValidationAgent (3 эшелона проверки)
**Статус**: Код есть, эшелоны 2-3 без LLM не работают
**Acceptance Criteria**:
- [x] `agents/brain/validation_agent.py`
- [x] Эшелон 1 (структурный фильтр) — работает без LLM
- [x] Эшелон 2 (LLM-анализ методологии) — нужен LLM
- [x] Эшелон 3 (консенсус-проверка) — нужен LLM
- [x] TrustLevel: HIGH/MEDIUM/LOW + ValidationCategory
- [ ] **Реальный тест**: подключить LLM провайдер и пройти статью через все 3 эшелона

---

### ½ Блок 50 — AggregatorAgent (эталонные статьи + сторителлинг)
**Статус**: Код есть, без LLM работает на fallback
**Acceptance Criteria**:
- [x] `agents/brain/aggregator_agent.py`
- [x] ConsolidatedArticle с полями: consensus, nuances, story, sources, confidence, controversy_level
- [x] LLM-генерация сторителлинга (с fallback)
- [x] LLM-анализ консенсуса/нюансов (с fallback)
- [x] Источник `[Источник_N]` + структурированные данные автора
- [ ] **Реальный тест**: пропустить 5 статей через агрегатор → получить ConsolidatedArticle со связным сторителлингом

---

### ½ Блок 51 — IntegratorAgent (встраивание без конфликтов)
**Статус**: Код есть
**Acceptance Criteria**:
- [x] `agents/brain/integrator_agent.py`
- [x] Детекция конфликтов через ключевые слова-маркеры
- [x] Стратегия разрешения: REPLACE / KEEP_BOTH / MERGE / SKIP
- [x] Помечает спорные темы как `disputed`
- [ ] **Реальный тест**: интегрировать 2 противоречащих статьи → правильное разрешение

---

### ½ Блок 52 — OrchestratorAgent (главный регулировщик)
**Статус**: Код есть
**Acceptance Criteria**:
- [x] `agents/brain/orchestrator_agent.py`
- [x] Decision: CREATE_MODULE / UPDATE_MODULE / AGGREGATE / REQUEST_MORE_DATA / SKIP
- [x] Расчёт статистики (high/medium/low) и pass_rate
- [x] Action plan и next_agent
- [ ] **Реальный тест**: пропустить 10 ValidationResult → получить корректное Decision

---

### ½ Блок 53 — ModuleBuilderAgent (генерация скиллов и Python-модулей)
**Статус**: Код есть, не тестировался
**Acceptance Criteria**:
- [x] `agents/brain/module_builder_agent.py`
- [x] Создание `backend/app/core/knowledge/<topic>.py` из ConsolidatedArticle
- [x] Создание `skills/<topic>.md`
- [x] Обновление `therapy_router.py` (добавление импорта + TOPIC_MAPPING)
- [ ] **Реальный тест**: пропустить 1 ConsolidatedArticle → получить рабочий .py модуль с `get_prompt_context()`

---

### ½ Блок 54 — ReReviewAgent (перепроверка через 3-6 мес)
**Статус**: Код есть, Retraction Watch не интегрирован
**Acceptance Criteria**:
- [x] `agents/brain/re_review_agent.py`
- [x] Загрузка статей с истёкшей next_review через KnowledgeBase
- [x] Расписание: 3 месяца → далее 6 месяцев
- [ ] Интеграция с Retraction Watch API
- [ ] LLM-проверка новых опровержений
- [ ] **Реальный тест**: запустить `python agents/runner.py --review`

---

### ⬜ Блок 55 — Запуск пайплайна агентов end-to-end ⭐
**Статус**: Не начато
**Зависимости**: Блоки 47-54 + Блок 2.5 (LLM API key)
**Acceptance Criteria**:
- [ ] `agents/runner.py` готов
- [ ] `pip install httpx pyyaml` выполнено
- [ ] PUBMED_EMAIL настроен в `.env`
- [ ] Запуск: `python agents/runner.py --topic "grief bereavement"` → в `knowledge_base/psychology/grief/` появляется новая эталонная статья
- [ ] Проверка качества сторителлинга (читать глазами)
- [ ] Проверка структуры YAML файла
- [ ] Логи на каждом шаге пайплайна (Researcher → Validator → Orchestrator → ...)

---

### ⬜ Блок 56 — Cultural Agents (после MVP)
**Статус**: Не начато (папка `agents/culture/` пуста, заглушка только)
**Зависимости**: Блоки 47-55 (опытная база агентов)
**Acceptance Criteria**:
- [ ] `agents/culture/cultural_collector.py` — сбор данных о российском культурном контексте
- [ ] `agents/culture/cultural_validator.py` — проверка на стереотипы
- [ ] `agents/culture/library_optimizer.py` — поддержание актуальности
- [ ] Источники: НКРЯ, этнографические исследования, Data Flywheel
- [ ] `knowledge_base/culture/ru/*.md` наполняется

---

## МОЗГ КАЙРОСА (статичные знания)

> Уже наполнено вручную из научных источников. См. `BRAIN_ARCHITECTURE.md`.

### ½ Блок 57 — knowledge/six_cs.py (SIX C's Фарчи)
**Статус**: Полностью наполнено (14 КБ)
**Acceptance Criteria**:
- [x] 6 компонентов модели Фарчи (Challenge, Control, Commitment, Continuity, Calmness, Confidence)
- [x] Техники, примеры вопросов, противопоказания
- [x] Функции для использования в промптах
- [ ] Подключено к `therapy_router.py` (нужно проверить)

---

### ½ Блок 58 — knowledge/who_pfa.py (ВОЗ PFA)
**Статус**: Полностью наполнено (15 КБ)
**Acceptance Criteria**:
- [x] Look, Listen, Link
- [x] Техники заземления (5-4-3-2-1, дыхание 4-4-6)
- [x] Источник: WHO Psychological First Aid Guide (2011)
- [ ] Подключено к промптам

---

### ½ Блок 59 — knowledge/cbt_techniques.py
**Статус**: Полностью наполнено (14 КБ)
**Acceptance Criteria**:
- [x] CBT техники и когнитивные искажения
- [ ] Подключено к промптам

---

### ½ Блок 60 — knowledge/dbt_skills.py
**Статус**: Полностью наполнено (17 КБ)
**Acceptance Criteria**:
- [x] DBT навыки (4 модуля: mindfulness, distress tolerance, emotion regulation, interpersonal effectiveness)
- [ ] Подключено к промптам

---

### ½ Блок 61 — knowledge/act_processes.py
**Статус**: Полностью наполнено (16 КБ)
**Acceptance Criteria**:
- [x] ACT процессы (Hexaflex)
- [ ] Подключено к промптам

---

### ½ Блок 62 — knowledge/sfbt_mi.py
**Статус**: Полностью наполнено (21 КБ)
**Acceptance Criteria**:
- [x] SFBT (Solution-Focused Brief Therapy) + Мотивационное консультирование
- [ ] Подключено к промптам

---

### ½ Блок 63 — knowledge/crisis_situations.py
**Статус**: 455+ ситуаций (207 КБ — самый большой файл проекта)
**Acceptance Criteria**:
- [x] Категории: суицид, паника, утрата, насилие, ПТСР, медработники, учителя, военные, мобилизация, эмиграция, беженцы и т.д.
- [x] Каждая ситуация: keywords + protocol
- [ ] Интегрировано с `crisis/detector.py` (сейчас detector использует только keywords.py)

**Что осталось**: связать crisis_situations.py с детектором для более тонкой типизации кризиса.

---

### ½ Блок 64 — therapy_router.py
**Статус**: Большой файл (19 КБ), не подключён к /api/chat
**Acceptance Criteria**:
- [x] `app/core/therapy_router.py` с TherapyRouter и TherapyState
- [x] Динамическая маршрутизация техник по distress_score и теме
- [x] `tests/test_therapy_router.py` существует (перенесён из корня backend/)
- [ ] Интеграция с Блоком 5 (`/api/chat`)
- [ ] Запустить тесты `pytest tests/test_therapy_router.py -v`

---

### ½ Блок 65 — user_memory/ (досье пользователя)
**Статус**: Полная структура есть (5 модулей + README), не подключено
**Acceptance Criteria**:
- [x] `app/core/user_memory/dossier.py` — структура досье
- [x] `app/core/user_memory/extractor.py` — LLM извлекает факты
- [x] `app/core/user_memory/compressor.py` — сжатие истории
- [x] `app/core/user_memory/storage.py`
- [x] `app/core/user_memory/updater.py`
- [x] `app/core/user_memory/README.md` (14 КБ документации)
- [ ] Интеграция с Блоком 6a (нужны таблицы users + dossiers в PostgreSQL)
- [ ] Интеграция с Блоком 5 (после каждого сообщения — обновлять досье)

---

## ИНФРАСТРУКТУРА РЕПО (Сессия 16)

### ✅ Блок 66 — git + .gitignore
**Статус**: Готово
**Acceptance Criteria**:
- [x] `.git/` существует (`git init` сделан вручную)
- [x] `.gitignore` создан с правилами для Python, Node, IDE, секретов, бэкапов
- [x] Игнорируются: `venv/`, `__pycache__/`, `.env`, `node_modules/`, `*.backup`, кэши

---

### ✅ Блок 67 — README.md
**Статус**: Готово
**Acceptance Criteria**:
- [x] Корневой `README.md` с описанием проекта
- [x] Раздел «Быстрый старт для AI-ассистента»
- [x] Раздел «Быстрый старт для разработчика»
- [x] Структура проекта
- [x] Технический стек
- [x] Текущий статус (что работает, что в работе)

---

### ✅ Блок 68 — Чистка корня + docs/research/
**Статус**: Готово (Сессия 16)
**Acceptance Criteria**:
- [x] Создана папка `docs/research/`
- [x] Перенесены: `infrastructure_budget.md`, `grants.md`, `research_protocol.md`
- [x] Удалены 9 устаревших .md из корня (CLAUDE.md.backup, CLAUDE_NEW.md, *_v2/v3/v4 и т.д.)
- [x] Удалены кэши: `.pytest_cache/`, `__pycache__/` в коде проекта
- [x] `test_therapy_router.py` перенесён из `backend/` в `backend/tests/`
- [x] `__init__.py` добавлены в `agents/`, `agents/brain/`, `agents/shared/`, `agents/culture/`
- [x] `tests/conftest.py` создан с базовыми fixtures
- [x] CLAUDE.md очищен от дублей и реструктурирован (Сессия 16.2 — восстановлены ошибочно удалённые секции «Два режима», «Карта пути», «Технический стек», «Монетизация», «Дорожная карта», «Юридические рамки», «Экосистема скиллов»)
- [x] PROGRESS.md обновлён со статусами и новыми блоками 47-69

---

## СКРИНИНГ И ОЦЕНКА (валидированные опросники)

### ⬜ Блок 69 — Скрининг ASQ + PSS-4 + ОСР
**Статус**: Не начато
**Зависимости**: Блок 5 (`/api/chat`) + Блок 6a (модели данных для записи результатов)

**Цель**: добавить валидированные опросники для:
1. Точной детекции суицидального риска (ASQ) — критично для безопасности
2. Количественной оценки стресса (PSS-4) — метрика для data flywheel (до/после)
3. Российский культурный контекст (ОСР Разуваевой)

**Acceptance Criteria**:
- [ ] `app/core/screening/asq.py` — Ask Suicide-Screening Questions (NIH)
  - 4 вопроса
  - Любой «Да» → переход на 5-й уточняющий + crisis routing immediate
- [ ] `app/core/screening/pss4.py` — Perceived Stress Scale (Cohen, 4 вопроса)
  - Шкала 0-4 для каждого вопроса
  - Сумма → уровень стресса
- [ ] `app/core/screening/osr.py` — Опросник Стрессовых Реакций (модификация Разуваевой, РФ)
- [ ] `app/api/screening.py` с эндпоинтами:
  - POST /api/screening/asq
  - POST /api/screening/pss4
  - POST /api/screening/osr
- [ ] Модель `ScreeningResult` в БД (привязка к session_id или user_id)
- [ ] Интеграция с `crisis/detector.py`:
  - ASQ положительный → принудительный `crisis_level = "immediate"` независимо от текста
- [ ] Интеграция с Путём А (карта пользователя): ASQ → PSS-4 → выбор ветки
- [ ] Тесты: `tests/test_screening.py`
  - ASQ: «Думали ли вы о смерти за последние недели?» (Да) → immediate
  - PSS-4: сумма ≥ 10 → high stress
  - ОСР: набор маркеров → конкретный тип реакции

**Подзадачи**:
1. Найти оригинальные опросники (общественное достояние, валидированы)
2. Перевести/адаптировать на русский если нужно
3. Создать модули скрининга
4. Создать эндпоинты
5. Интегрировать с crisis detector
6. Интегрировать с user journey (Путь А)
7. Написать тесты

**Источники**:
- ASQ: NIH (https://www.nimh.nih.gov/research/research-conducted-at-nimh/asq-toolkit-materials)
- PSS-4: Cohen S. (1988). Perceived Stress in a Probability Sample of the United States.
- ОСР: Разуваева Т.Н. (модификация для российского контекста)

**Юридическая ценность**: использование валидированного скрининга = **аргумент в спорах** с грантодателями («у нас не отсебятина, а признанные методики») и **усиление защиты по ФЗ-152** (показывает что мы серьёзно относимся к работе со специальной категорией ПДн).

---

## Статистика

**Всего блоков**: 77 (включая под-блоки 1.5, 2.5, 5.5, 6a/b/c/d, 12.5, 16.5)

| Статус | Количество | Что значит |
|---|---|---|
| ✅ Завершено | 3 | Блоки 66, 67, 68 (инфраструктура репо, Сессия 16) |
| ½ Код есть, не протестирован | 22 | Блоки 1, 1.5, 2, 3, 4, 47-54, 57-65 |
| ¼ Частично сделано | 1 | Блок 8 (2 из 5 компонентов фронта) |
| ⬜ Не начато | 51 | Всё остальное (включая Блок 5 — главный gap, и новый Блок 69 — Скрининг) |

**Прогресс по реальному коду** (½ + ¼ + ✅): **~34%** (26 из 77)
**Прогресс по «боевому» состоянию** (только ✅): **~4%** (3 из 77)

> **Главный gap**: Блок 5 (`/api/chat`) — без него ничего не работает end-to-end.
> Без этого блока 22 уже написанных «½» останутся в подвешенном состоянии.

---

## Следующие шаги (приоритеты)

### Критический путь к работающему MVP

1. **⭐ Блок 5** — `/api/chat` endpoint (главный пробел!)
   - Связать crisis detector + prompt builder + LLM provider
   - Протестировать полный поток: сообщение → ответ
   - Без этого никакой фронтенд не имеет смысла

2. **Блок 2.5** — Подключить реальный LLM API
   - Получить ключ Yandex Cloud AI Studio (или Cloud.ru — бесплатно)
   - Прописать в `.env`
   - Запустить `tests/test_llm.py`

3. **Блок 6a** — Модели данных + БД + Alembic
   - Без БД нет data flywheel
   - Можно использовать удалённый PostgreSQL на VPS (Блок 18)

4. **Блок 7** — Next.js каркас
   - Сохранить 2 готовых компонента
   - `npx create-next-app` в `frontend/`

5. **Блок 8** — Чат-интерфейс
   - Доделать оставшиеся 3 компонента + хук `useChat`

6. **Блок 69** — Скрининг ASQ + PSS-4 + ОСР
   - **Критично для безопасности**: ASQ ловит суицидальный риск точнее, чем keyword-детектор
   - Метрика для data flywheel (PSS-4 до/после = улучшилось ли состояние)
   - Юридическое усиление (валидированные опросники)
   - Делать **после Блока 5** (нужен POST endpoint) и **Блока 6a** (нужна модель `ScreeningResult`)

### Параллельно

- **Блок 12.5** — прогнать существующие тесты (`pytest`) — узнать что реально работает
- **Блок 55** — протестировать пайплайн агентов end-to-end (когда будет API key)

### После MVP

- Блоки 12 (NLP), 13-15 (auth), 23-25 (платежи), 22 (самозанятый)
- Блоки 47-56 (агенты в продакшен)

---

*Последнее обновление: Сессия 16, Апрель 2026*
*История правок:*
- *16.1: чистка корня + структура + блоки 47-68 (агенты, мозг, инфра репо)*
- *16.2: добавлен Блок 69 (Скрининг ASQ + PSS-4 + ОСР), исправлены ссылки на удалённые файлы*

*Версия: 2.2*
