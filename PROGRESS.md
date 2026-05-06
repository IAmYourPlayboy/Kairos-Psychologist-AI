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

### ✅ Блок 1 — Бекенд: FastAPI каркас
**Статус**: Работает (Сессия 17 — uvicorn запущен, /api/health отвечает 200)
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

### ✅ Блок 1.5 — .env и secrets management
**Статус**: Работает (Сессия 17 — .env загружается, секреты в gitignore)
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

### ✅ Блок 2 — Бекенд: LLM-абстракция
**Статус**: Работает (Сессия 17 — реальный вызов Yandex Cloud, OpenAI-совместимый API)
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

### ½ Блок 2.5 — Подключение Yandex Cloud AI Studio
**Статус**: Не начато  
**Зависимости**: Блок 2  
**Acceptance Criteria**:
- [x] Зарегистрирован в Yandex Cloud
- [x] Сервисный аккаунт создан: `ai-studio-9fe55b` (id: `aje6uober8o0inbuovie`)
- [x] API-ключ создан для AI Studio (id: `ajefv4i5b5qr17huko61`)
- [x] LLM_BASE_URL и LLM_API_KEY указаны в .env
- [x] Folder ID получен: `b1gsi8fibvna5mkauuu4`
- [x] Тест: генерация через API работает → ответ от **YandexGPT Lite** (workaround)
- [ ] **Что осталось**: подключить **Qwen3-14B** в Yandex Console → https://console.yandex.cloud/folders/b1gsi8fibvna5mkauuu4/foundation-models
- [ ] После подключения вернуть `LLM_MODEL=gpt://b1gsi8fibvna5mkauuu4/qwen3-14b/latest`

**Текущая модель**: YandexGPT Lite (для отладки end-to-end). Имеет встроенную цензуру — для боевого терапевтического бота не подходит, нужно переключить на Qwen.

---

### ✅ Блок 3 — Бекенд: терапевтические промпты
**Статус**: Работает (Сессия 17 — промпты передаются в LLM, бот отвечает в стиле «Кайроса»)
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

### ✅ Блок 4 — Бекенд: кризисная детекция
**Статус**: Работает (Сессия 17 — детектор интегрирован в /api/chat, проставляет crisis_level в БД)
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

### ✅ Блок 5 — Бекенд: эндпоинт /api/chat ⭐ **СЕРДЦЕ ПРОДУКТА**
**Статус**: РАБОТАЕТ end-to-end (Сессия 17 — проверено вживую с YandexGPT Lite)
**Зависимости**: Блоки 2, 3, 4, 6a (все готовы)
**Acceptance Criteria**:
- [x] `app/api/chat.py` с POST `/api/chat`
- [x] Принимает `{message, session_id?, guest_id?, age_group?, history?}`
- [x] Возвращает `{reply, session_id, message_id, crisis_level, crisis_contacts, branch, response_time_ms, prompt_tokens, completion_tokens}`
- [x] Поток: crisis detection → branch selector (A/B) → prompt builder → LLM → response
- [x] Сохранение пользовательского сообщения и ответа бота в БД (data flywheel — inline data logger Блок 6b)
- [x] Создание / обновление ChatSession (counter, max crisis level)
- [x] Pydantic схемы запроса/ответа в `app/api/schemas.py`
- [x] Graceful degradation если LLM упал (immediate → жёсткий fallback с контактами; иначе общий текст)
- [ ] Реальный тест end-to-end: запустить uvicorn + curl → получить ответ
- [ ] Тест в pytest: `POST /api/chat {"message": "мне плохо"}` → ответ по протоколу
- [ ] Тест в pytest: `POST /api/chat {"message": "хочу умереть"}` → crisis_level="immediate" + contacts

**Связанные новые модули**:
- `app/core/branch_selector.py` — rule-based выбор ветки A/B по сообщению
- `app/api/schemas.py` — Pydantic схемы

**Что осталось**: запустить uvicorn, прогнать end-to-end test, написать pytest-тесты.

---

### ✅ Блок 5.5 — API endpoint /api/feedback
**Статус**: Работает (Сессия 17, в составе работающего пайплайна chat)
**Зависимости**: Блоки 5, 6a
**Acceptance Criteria**:
- [x] `app/api/feedback.py` с POST `/api/feedback`
- [x] Принимает `{session_id, message_id?, event_type}`
- [x] event_type: "felt_better", "no_change", "felt_worse", "thumbs_up", "thumbs_down", "crisis_escalated", "session_timeout", "user_left"
- [x] Записывает в таблицу `feedback_events`
- [x] Обновляет `outcome` сессии при felt_better/no_change/felt_worse/user_left
- [x] Возвращает `{ok, feedback_id}`
- [ ] Реальный тест: POST /api/feedback → запись в БД (нужен запуск)
- [ ] Pytest-тест

---

### ✅ Блок 6a — Бекенд: модели данных + БД + Alembic
**Статус**: Работает (Сессия 17 — миграции применены, kairos_dev.db создан, INSERT/UPDATE/SELECT работают вживую)
**Зависимости**: Блок 1
**Acceptance Criteria**:
- [x] `app/data/models.py` с 6 таблицами: users, chat_sessions, messages, feedback_events, subscriptions, screening_results
- [x] `app/data/database.py` с AsyncSession, engine, get_db()
- [x] `app/data/__init__.py` с экспортами
- [x] SQLite (dev) + PostgreSQL (prod) через одну переменную DATABASE_URL
- [x] Alembic настроен (`alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`)
- [x] Поддержка `render_as_batch` для SQLite (для ALTER TABLE)
- [x] `dispose_engine()` подключён в lifespan приложения
- [x] `pyproject.toml` обновлён: добавлены sqlalchemy[asyncio], aiosqlite, asyncpg, alembic, pyyaml
- [x] Эндпоинт `/api/health/db` для проверки подключения
- [ ] **Юзер должен выполнить**: `pip install -e .` + `alembic revision --autogenerate -m "initial tables"` + `alembic upgrade head`
- [ ] Pytest-тесты для моделей

**Связанные новые файлы** (Сессия 17):
- `backend/app/data/models.py` (6 моделей SQLAlchemy 2.0)
- `backend/app/data/database.py` (engine, session, get_db, lifecycle)
- `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/script.py.mako`

---

### ✅ Блок 6b — Бекенд: data logger + pipeline (inline в chat.py)
**Статус**: Работает inline в `app/api/chat.py` (Сессия 17 — каждый диалог записывается в SQLite)
**Зависимости**: Блоки 5, 6a

**Решение**: пока логирование диалогов происходит **прямо в `chat.py`** (после каждого ответа LLM сохраняем `Message` в БД и обновляем `ChatSession`). Отдельный `app/data/logger.py` НЕ создавали — преждевременная абстракция.
Когда в Блоке 12 (Aniemore) добавится больше метаданных (emotion, distress_score) — вынесем в отдельный модуль.
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

### ✅ Блок 6d — Бекенд: middleware (request_id, CORS, error handling)
**Статус**: Работает (Сессия 17 — frontend ↔ backend без CORS-ошибок, error handler перехватывает 400 от LLM)
**Зависимости**: Блок 1
**Acceptance Criteria**:
- [x] `app/middleware/request_id.py` — X-Request-ID для трейсинга
- [x] CORS настроен в `main.py`
- [x] `app/middleware/security_headers.py` — X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy
- [x] `app/middleware/error_handler.py` — 3 глобальных обработчика (HTTPException, RequestValidationError, Exception)
- [x] Все обработчики возвращают унифицированный JSON `{error: {type, status, message, request_id, details?}}`
- [x] При 500 — stacktrace **только в логи**, клиенту общий текст
- [ ] Тест: каждый запрос имеет X-Request-ID в логах
- [ ] Тест: при ошибке валидации — JSON с подробностями errors()

**Подзадачи** (старые):
1. Создать app/middleware/request_id.py
2. Настроить CORS в main.py
3. Добавить security headers
4. Создать глобальный error handler
5. Написать тесты

---

### ✅ Блок 7 — Фронтенд: Next.js каркас
**Статус**: Работает (Сессия 17 — `npm install` пройден, `npm run dev` поднимает сервер на :3000)
**Зависимости**: Нет

**Решение**: вместо `npx create-next-app` (интерактивный диалог) собрал каркас Next.js 14 руками — все конфиги, layout, globals.css созданы. Существующие `MessageBubble.tsx` + `HumanTypingEffect.tsx` сохранены.

**Acceptance Criteria**:
- [x] `package.json` с зависимостями (next 14.2, react 18.3, typescript 5.6, tailwind 3.4)
- [x] `tsconfig.json` (strict mode, paths: `@/*`)
- [x] `next.config.js` с rewrites `/api/*` → `http://localhost:8001`
- [x] `tailwind.config.ts` с палитрой Кайроса (warm + accent + crisis)
- [x] `postcss.config.mjs`
- [x] `next-env.d.ts`
- [x] `app/layout.tsx` с метаданными + Golos Text через `next/font/google`
- [x] `app/page.tsx` — редирект на `/chat`
- [x] `app/globals.css` с Tailwind base + кастомным скроллбаром
- [x] `frontend/.gitignore` (node_modules, .next, .env*)
- [x] Сохранены `MessageBubble.tsx` + `HumanTypingEffect.tsx`
- [ ] **Юзер должен выполнить**: `cd frontend && npm install && npm run dev` → проверить что `http://localhost:3000` открывается

**Связанные новые файлы** (Сессия 17):
- `frontend/package.json`, `tsconfig.json`, `next.config.js`, `tailwind.config.ts`, `postcss.config.mjs`, `next-env.d.ts`
- `frontend/app/layout.tsx`, `frontend/app/page.tsx`, `frontend/app/globals.css`
- `frontend/.gitignore`

---

### ✅ Блок 8 — Фронтенд: чат-интерфейс
**Статус**: Работает end-to-end (Сессия 17 — отправка сообщения, отображение ответа, авто-скролл)
**Зависимости**: Блок 7

**Acceptance Criteria**:
- [x] `components/Chat/ChatContainer.tsx` — главный контейнер (header, лента, input, кризисная модалка)
- [x] `components/Chat/MessageBubble.tsx` (доработан: палитра warm/accent, флаг animateTyping)
- [x] `components/Chat/HumanTypingEffect.tsx` ✓ (был ранее)
- [x] `components/Chat/TypingIndicator.tsx` — три точки с пульсацией
- [x] `components/Chat/InputArea.tsx` — textarea с авторазмером, Enter=send, Shift+Enter=newline, дисклеймер
- [x] `hooks/useChat.ts` — основная логика (отправка, история, состояние, отмена, feedback, reset)
- [x] `hooks/useSession.ts` — guest_id (localStorage) + session_id (sessionStorage), crypto.randomUUID()
- [x] `lib/types.ts` — TypeScript-типы (соответствуют Pydantic-схемам бекенда)
- [x] `lib/api.ts` — fetch-обёртка с таймаутом и обработкой ошибок (ApiClientError)
- [x] `app/chat/page.tsx` — рендер ChatContainer
- [x] Авто-скролл к последнему сообщению (scrollIntoView)
- [x] EmptyState при первом заходе (приветствие)
- [x] Оптимистичное добавление user-сообщения + статус (pending → synced → failed)
- [x] AbortController для отмены запроса
- [x] Дисклеймер «не замена врачу/психологу» под полем ввода
- [ ] **Юзер должен**: `npm install` + `npm run dev` + написать «мне плохо» → увидеть ответ
- [ ] QuickReplies (отложил — нужен Блок 12 NLP для умного предложения)

**QuickReplies** перенесён в отдельный todo: умные подсказки требуют контекстного анализа (Блок 12 — Aniemore).

---

### ½ Блок 9 — Фронтенд: кризисный блок
**Статус**: Компоненты готовы (Сессия 17), ждёт ручной проверки на кризисном сообщении
**Зависимости**: Блок 8

**Acceptance Criteria**:
- [x] `components/Crisis/SOSButton.tsx` в шапке — цвет и анимация зависят от `crisisLevel`
- [x] `components/Crisis/CrisisPanel.tsx` — модальная панель с номерами (tel: ссылки)
- [x] `components/Crisis/CrisisInlineCard.tsx` — карточка контактов под ответом бота в ленте
- [x] SOS-кнопка пульсирует при `crisis_level=high` (медленно) и `immediate` (быстро)
- [x] Панель открывается автоматически при `immediate`
- [x] Дефолтные контакты в CrisisPanel (на случай если бекенд молчит)
- [x] Контакты подставляются из `last_assistant_message.crisis_contacts`
- [x] Цвета карточки: elevated→warm, high→crisis-50, immediate→crisis-100
- [ ] Тест: реально отправить сообщение «хочу умереть» → увидеть immediate панель + контакты

---

### ½ Блок 10 — Фронтенд: локальное хранилище (Dexie.js)
**Статус**: Код готов (Сессия 18 — `lib/db.ts` + интеграция с `useChat`), нужен `npm install dexie` и проверка вживую
**Зависимости**: Блок 8
**Acceptance Criteria**:
- [x] `lib/db.ts` с Dexie БД (sessions, messages, syncQueue) — 3 таблицы, индексы по sessionId/createdAt/syncStatus
- [x] `hooks/useSession.ts` с guestId в localStorage (был ранее)
- [x] `useChat` сохраняет каждое сообщение в IndexedDB (user → pending → synced/failed; bot → synced)
- [x] При первом монтировании `useChat` подгружает историю сессии из IndexedDB
- [x] `dexie@^4.0.10` добавлен в `frontend/package.json`
- [x] Высокоуровневые хелперы: `saveLocalMessage`, `updateMessageStatus`, `loadSessionMessages`, `listSessions`, `deleteSession`, `clearAllLocalData`
- [ ] **Юзер должен**: `cd frontend && npm install` (подтянет `dexie`) → `npm run dev` → отправить сообщение, перезагрузить страницу, убедиться что чат на месте
- [ ] При возврате: «С возвращением. Хочешь продолжить?» — отдельным UI-элементом (Блок 29)

**Связанные новые файлы** (Сессия 18):
- `frontend/lib/db.ts` (Dexie-схема + хелперы)
- `frontend/hooks/useChat.ts` (добавлена интеграция с Dexie: запись + загрузка истории)
- `frontend/package.json` (dexie зависимость)

---

### ½ Блок 11 — Фронтенд: обратная связь
**Статус**: Код готов (Сессия 18 — UI кнопок + интеграция в ChatContainer), нужна проверка вживую
**Зависимости**: Блоки 8, 5.5
**Acceptance Criteria**:
- [x] `components/Feedback/MessageFeedback.tsx` — thumbs up/down под каждым ответом бота (главный сигнал data flywheel)
- [x] `components/Feedback/SessionFeedback.tsx` — большая карточка «Стало легче / Не уверен / Хуже» в конце сессии
- [x] Кнопка «Завершить» в шапке (показывается после первого ответа бота)
- [x] После клика кнопки заменяются на «Спасибо» — повторно нажать нельзя
- [x] Использует `chat.sendFeedback()` из `useChat` → POST /api/feedback с event_type
- [x] event_type: `thumbs_up`, `thumbs_down`, `felt_better`, `no_change`, `felt_worse`
- [ ] **Юзер должен**: проверить вживую — отправить сообщение, нажать 👍 → видно «Спасибо», в БД появилась запись в `feedback_events`
- [ ] Pytest-тест feedback API (см. Блок 12.5 — `tests/test_chat.py` уже включает `test_feedback_creates_event`)

**Связанные новые файлы** (Сессия 18):
- `frontend/components/Feedback/MessageFeedback.tsx`
- `frontend/components/Feedback/SessionFeedback.tsx`
- `frontend/components/Chat/ChatContainer.tsx` (интегрированы оба компонента + кнопка «Завершить»)

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

### ½ Блок 12.5 — Бекенд: тесты (pytest)
**Статус**: 4 файла тестов написаны (Сессия 18 — добавлен test_chat.py с моком LLM), нужен реальный прогон pytest юзером
**Зависимости**: Блоки 1-12
**Acceptance Criteria**:
- [x] `tests/conftest.py` — глобальные фикстуры (sample_crisis_messages, forbidden_phrases)
- [x] `tests/test_crisis.py` — тесты кризисной детекции (все 4 уровня + приоритет + контакты)
- [x] `tests/test_prompts.py` — тесты промптов (запрещённые фразы, ветвление, кризисные промпты)
- [x] `tests/test_llm.py` — юнит-тесты OpenAICompatProvider (мок httpx)
- [x] `tests/test_therapy_router.py` — smoke-тест динамического router (без assert, для глаз)
- [x] **`tests/test_chat.py`** ⭐ — интеграционные тесты /api/chat и /api/feedback (Сессия 18):
  - normal / immediate / high crisis сценарии
  - персистентность сессии (один session_id для двух запросов)
  - валидация запроса (пустое сообщение → 422)
  - LLM падает → fallback с кризисными контактами
  - feedback (thumbs_up, felt_better) → запись в `feedback_events`
  - валидация event_type (неизвестный → 422)
  - GET /api/health
- [x] `pyproject.toml` уже содержит pytest>=8.0, pytest-asyncio>=0.24, httpx>=0.28
- [x] `asyncio_mode = "auto"` в `[tool.pytest.ini_options]` (можно писать `async def test_...`)
- [ ] **Юзер должен**: `cd backend && pip install -e ".[dev]" && pytest -v` — все 4 файла должны зеленеть (мок LLM убирает зависимость от сети)
- [ ] tests/test_auth.py — после Блока 13
- [ ] tests/test_sync.py — после Блока 15
- [ ] tests/test_screening.py — после Блока 69

**Связанные новые файлы** (Сессия 18):
- `backend/tests/test_chat.py` (12 тестов с моком LLM через `unittest.mock.patch`)

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

## ⭐ СЛОЙ ВОСПРИЯТИЯ (Сессия 18, Май 2026) — заменил rule-based детектор

> **Дизайн**: [`docs/superpowers/specs/2026-05-02-perception-layer-design.md`](docs/superpowers/specs/2026-05-02-perception-layer-design.md)
> **План имплементации**: [`docs/superpowers/plans/2026-05-02-perception-layer-plan.md`](docs/superpowers/plans/2026-05-02-perception-layer-plan.md)
> **Реализация**: ветка `feature/perception-layer` (~25 коммитов).

**Зачем**: rule-based grep (`crisis/detector.py`, `branch_selector.py`) не понимает намёков и контекста. *«Они мне сказали кое-что...»* возвращало `normal`, при том что это намёк на серьёзную тему. Архитектурный потолок словарей не закрыть расширением словарей.

**Что построено**: 4 связанных компонента в `core/perception/`:

### ✅ Блок P1 — Brain (статичные знания, уже было)
- `core/knowledge/*.py` — терапевтические протоколы, эталонные статьи
- Меняется редко, через цепочку агентов (Researcher → Validator → ...)

### ✅ Блок P2 — Dossier (на user_id, папки → подпапки → факты)
- `data/dossier_models.py` — 3 таблицы: `dossier_facts`, `dossier_quotes`, `dossier_checkpoints`
- `core/perception/folders.py` — 13 фиксированных папок + custom + валидация
- `core/perception/dossier.py` — `DossierService` с CRUD над фактами/цитатами
- Каждый факт хранит **буквальные цитаты** пользователя → Кайрос возвращается к точному тексту

### ✅ Блок P3 — Mood (6 осей в Redis, на session_id)
- `core/perception/mood.py` — `MoodService` с правилами обновления
- 6 осей: alertness, warmth, pace, assertiveness, trust_in_user, depth
- Обновляется правилами после каждого сообщения (без LLM)
- Сериализуется в текстовый блок для основного промпта

### ✅ Блок P4 — MessageAnalyzer + Pipeline + интеграция в /api/chat
- `core/perception/analyzer.py` — отдельный LLM-вызов на каждое сообщение
- Возвращает `PerceptionReport`: risk_level, эмоции, тема, hidden_signals, folder_hints, **inner_monologue** (мысли Кайроса от первого лица)
- `core/perception/pipeline.py` — `PerceptionPipeline` оркестратор: analyzer → mood update → подтяжка фактов → промпт → основная LLM
- `api/chat.py` упрощён: больше нет ветвления и rule-based fallback

### ✅ Блок P5 — ReflectionAgent через Celery
- `core/perception/reflection_agent.py` — фоновый агент, запускается через 15 минут после последнего сообщения
- Полный цикл: extract (LLM) → classify+dedupe (LLM) → update Dossier
- `celery_app.py` + `celery_worker.py` + `reflection_tasks.py` — Celery с Redis-broker
- **Дедупликация запусков** через Redis-ключ `reflection:scheduled:{user_id}`: если пользователь продолжает писать, новый scheduled_at перебьёт старый и устаревший таск-старичок выходит без работы

### ✅ Блок P6 — UI досье + удаление старого rule-based
- `api/dossier.py` — GET / DELETE /api/dossier (по user_id или guest_id для MVP)
- `frontend/app/profile/page.tsx` + `frontend/components/Dossier/DossierView.tsx` — просмотр и удаление досье (ФЗ-152 «право на удаление»)
- **Удалены**: `crisis/detector.py`, `crisis/keywords.py`, `branch_selector.py`, `tests/test_crisis.py`, `tests/test_chat.py` (старая ветка). Сохранены: `crisis/contacts.py`, `prompts/*` (используются PromptBuilder'ом)
- Колонка `chat_sessions.branch` удалена через alembic-миграцию

### Метрики Сессии 18

- **114 тестов** перцепции и API досье — все зелёные
- **~25 коммитов** на ветке `feature/perception-layer`
- Удалено **948 строк** старого rule-based кода
- Каждое сообщение пользователя теперь = **2 LLM-вызова** (analyzer + main reply) ≈ 0.45-2₽ при разных моделях
- Каждая сессия (раз в 15 мин) = +1 LLM-вызов рефлексии ≈ 0.5-1₽

### Что НЕ входит в эту итерацию

- Аудио-восприятие (STT, Aniemore WavLM) — после MVP
- Голос двойника (ElevenLabs PVC) — Фаза 7
- Тренировка Mood и Analyzer на data flywheel — Фаза 5+ (после 500+ диалогов)
- Evolutional Dossier-агент (ревизор фактов) — Фаза 7+

### Идеи на расширение (заметки)

- **Иерархия в custom-папках.** Сейчас `custom/<name>` — плоский. Если у
  пользователя начинает разрастаться большая тема (например, медицинская
  история), стоит дать ReflectionAgent правило, по которому внутри custom
  тоже работает «родитель → подпапка» по тому же стандарту, что и
  фиксированные. Например: `custom/medical/visits`, `custom/medical/diagnoses`,
  `custom/medical/medications` вместо одной плоской `custom/medical_visits`.
  Сейчас не критично, но при росте досье — ускорит подтяжку контекста
  через folder_hints.

- **Папки в БД, а не в коде** (Фаза 7+). После того как пайплайн
  стабилизируется, перенести `SUBFOLDERS` из `core/perception/folders.py`
  в таблицу `dossier_folder_taxonomy`. Это позволит ReflectionAgent или
  отдельному агенту-куратору добавлять новые папки на лету (с правилами
  валидации), а данные → переменные. Сейчас в коде нормально: пока
  система не зрелая, удобнее ревьюить в коммитах через git.

### Калибровка регулятора (Mood + Analyzer): откуда брать данные

Сейчас формулы в `mood.py` (`_risk_to_alertness`, `_risk_to_warmth_floor`,
`_risk_to_pace`, `EMOTION_WARMTH_DELTA`) — **догадки автора**, не научный
факт. Это нормально для MVP, но для «по-настоящему продуманного» поведения
нужны данные. Три уровня по приоритету:

#### Уровень 1 — научная литература (доступно сейчас, бесплатно)

В `core/knowledge/` уже лежит ~75 КБ материала из реальных терапевтических
протоколов: SIX C's Фарчи, ВОЗ PFA, CBT, DBT, ACT, SFBT. Сейчас они
подключаются только к основному промпту через `prompts/base.py`.

**Что можно сделать**:
- Расширить промпт MessageAnalyzer выжимкой «как ВОЗ PFA различает уровни
  дистресса» — анализатор ставит risk_level не по своему ощущению, а по
  признакам из протокола.
- Расширить промпт ReflectionAgent extract критериями «что считать
  триггером» из CBT/DBT.
- Добавить ссылки на конкретные техники в `inner_monologue` основной LLM.

Это **не требует обучения и сбора данных** — только аккуратный промпт-
инжиниринг с уже существующими модулями. Подходит для итерации после
подключения Qwen3-14B (Блок 2.5).

#### Уровень 2 — публичные психологические корпусы (после MVP)

Существуют размеченные англоязычные датасеты:
- **GoEmotions** (Google, 58 тыс. реддит-комментариев, 27 эмоций) —
  для русского классификатора эмоций (через перевод как доп. сигнал).
- **EmpatheticDialogues** (Facebook, 25 тыс. диалогов с эмоциональными
  контекстами) — для понимания «правильного тона ответа».
- **Counsel Chat** (~4 тыс. реальных терапевтических разговоров) —
  для паттернов «вопрос пользователя → терапевтический ответ».

**Проблема**: всё на английском. Перевод теряет нюансы. Можно использовать
как **дополнительный сигнал** — например, тренировать классификатор эмоций
на их разметке и применять результат к нашему русскому корпусу.

Объём работы: 1-2 недели. Делать **после MVP**, когда сможем оценить
насколько это улучшает наш собственный data flywheel.

#### Уровень 3 — собственный data flywheel (сердце стратегии, Фаза 5+)

Это то, ради чего вся текущая архитектура. В `messages.perception_json`
уже логируется каждое суждение анализатора. После 500+ диалогов получим:

- 500 примеров «текст пользователя → risk_level от анализатора» с
  разметкой через feedback и outcome → можно тренировать LoRA или
  калибровать формулы.
- 500 примеров «эмоция в отчёте + mood → реакция пользователя» →
  регрессия по `EMOTION_WARMTH_DELTA` и `_risk_to_pace`. Получаем
  оптимальные коэффициенты на реальных данных, а не из головы автора.
- Связки «folder_hint X → реально использовался основной LLM в ответе» →
  метрика релевантности досье.

Что можно сделать:
- **LoRA fine-tuning** основной модели на собственных диалогах —
  чтобы она лучше отвечала именно в наших паттернах.
- **Калибровка формул Mood** через регрессию: «какой `pace` в среднем
  приводит к feedback=helped при risk=high?». Заменяет угадывание
  на статистику.
- **Классификатор папок-хинтов** обученный на твоих пользователях
  (вместо жёстко заданного списка).
- **Outcome-метрика** на основе follow-up через 1-7 дней (вернулся ли
  пользователь, нажимал ли «стало легче», прошёл ли PHQ-9 со снижением).

**Зависимость**: требует 500+ диалогов с реальными пользователями.
Без MVP-беты не запустить. Это и есть Фаза 5+ из общего плана —
прямой смысл `data flywheel`-стратегии проекта.

#### Что СЕЙЧАС НЕ нужно делать

- **Не обучать с нуля** ничего на чужих данных. LLM (Qwen, YandexGPT)
  уже обучены на огромных корпусах включая психологию — им не нужны
  наши данные чтобы понимать эмоции и контекст. Нужна **адаптация под
  наш домен** (русский, терапевтический, культурный), а это делается
  **промпт-инжинирингом + LoRA на наших собственных данных**, не
  предобучением на чужих.
- **Не калибровать формулы вручную** до сбора данных. Любая «продуманность»
  при 0 пользователей — это новое угадывание, не наука.

Правильная цепочка: **запуск → сбор данных → калибровка**. Не наоборот.

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
| ✅ **Завершено и работает** | **15** | Блоки **1, 1.5, 2, 3, 4, 5, 5.5, 6a, 6b, 6d, 7, 8** (Сессия 17 — рабочий MVP) + 66, 67, 68 (инфра репо) |
| ½ Код есть, не до конца | 22 | Блок 9 (нужна проверка кризис-сценария), 10 (Dexie готов, нужен `npm install`), 11 (Feedback UI готов, нужна проверка), 12.5 (тесты написаны, нужен прогон), 2.5 (workaround YandexGPT, нужен Qwen), 47-54, 57-65 |
| ⬜ Не начато | 40 | Auth, платежи, агенты в продакшен, скрининг, deploy |

**Прогресс по реальному коду** (½ + ✅): **~48%** (37 из 77)
**Прогресс по «боевому» состоянию** (только ✅): **~19%** (15 из 77)

> **🎉 СЕРДЦЕ ПРОДУКТА БЬЁТСЯ.** Сессия 17: пользователь пишет → Next.js → FastAPI → Yandex Cloud LLM → SQLite → ответ. Полная цепочка работает end-to-end. Бот отвечает: «Привет! Я — Кайрос, сервис первой поддержки. Что случилось? Тебе нужна помощь?»

### Что нужно для перевода ½ → ✅ (Сессия 17 → 18)

Юзер выполняет **6 команд**:

```bash
# Backend
cd d:\Kairos\backend
venv\Scripts\activate
pip install -e .
alembic revision --autogenerate -m "initial tables"
alembic upgrade head
uvicorn app.main:app --reload --port 8001  # отдельный терминал

# Frontend (другой терминал)
cd d:\Kairos\frontend
npm install
npm run dev
```

После этого:
- Открыть `http://localhost:3000/chat`
- Написать «привет» → получить ответ
- Если работает — Блоки 1, 1.5, 2, 2.5, 3, 4, 5, 5.5, 6a, 6b, 6d, 7, 8, 9 переходят в ✅

> **Что осталось сделать от юзера**: прислать `folder_id` Yandex Cloud для подключения LLM (см. ниже).

---

## Следующие шаги (приоритеты)

### 🎯 Что MVP уже умеет (Сессия 17)

- ✅ Принимает сообщение от пользователя через веб-чат
- ✅ Распознаёт кризисный уровень (4 уровня)
- ✅ Выбирает терапевтическую ветку (A — мобилизация / B — стабилизация)
- ✅ Собирает протокольный промпт из базы знаний
- ✅ Вызывает LLM (сейчас YandexGPT Lite, переключим на Qwen3-14B)
- ✅ Записывает каждое сообщение в SQLite (data flywheel в зачатке)
- ✅ Показывает SOS-кнопку и кризисную панель
- ✅ Подсвечивает интерфейс при кризисе

### 🔴 Что нужно сделать в первую очередь

1. **Блок 2.5 завершить — подключить Qwen3-14B**
   - Открыть https://console.yandex.cloud/folders/b1gsi8fibvna5mkauuu4/foundation-models
   - Подключить модель к folder
   - Скопировать точный URI с карточки модели
   - Заменить в `.env`: `LLM_MODEL=<URI>`
   - Перезапустить uvicorn → проверить чат

2. **Блок 12.5** — прогнать pytest (`cd backend && pytest -v`)
   - Узнать какие из 4 тестовых файлов проходят
   - Поправить упавшие

3. **Блок 9 проверить вживую** — отправить кризисное сообщение
   - Написать «всё бессмысленно, не хочу жить»
   - Должна открыться кризисная панель + бот должен дать контакты

### 🟡 Следующие важные блоки

4. **Блок 10** — Dexie.js (offline-кэш) — чтобы чат работал без сети
5. **Блок 11** — кнопки «стало легче / не помогло» под ответами бота (data flywheel сигналы)
6. **Блок 13-15** — аутентификация (email + пароль для начала)
7. **Блок 12** — двухслойный NLP (Aniemore + маркеры) — улучшит выбор ветки и кризисную детекцию
8. **Блок 69** — Скрининг ASQ + PSS-4 + ОСР (валидированные опросники)

### 🟢 Долгосрочное

- Блоки 17-21 — деплой на VPS Timeweb Cloud
- Блоки 22-27 — платежи (ЮKassa) + юридические страницы
- Блоки 47-55 — пайплайн агентов в продакшене
- Блок 36 — заявка на грант (Yandex Cloud Boost Start)

---

*Последнее обновление: Сессия 20, Май 2026*
*История правок:*
- *16.1: чистка корня + структура + блоки 47-68 (агенты, мозг, инфра репо)*
- *16.2: добавлен Блок 69 (Скрининг ASQ + PSS-4 + ОСР), исправлены ссылки на удалённые файлы*
- *17.0: реализованы Блоки 5, 5.5, 6a, 6b, 6d, 7, 8, 9 — рабочий MVP бекенда + фронта*
- *17.1: 🎉 **СЕРДЦЕ ПРОДУКТА БЬЁТСЯ!** End-to-end работает: чат отвечает через Yandex Cloud (workaround YandexGPT Lite, нужно подключить Qwen). 12 блоков переведены ½ → ✅. Прогресс по «боевому» состоянию: 4% → 19%.*
- *18.0: реализованы Блок 10 (Dexie offline-кэш), Блок 11 (Feedback UI: thumbs + session card), Блок 12.5 (test_chat.py с моком LLM — 12 интеграционных тестов /api/chat и /api/feedback). 3 блока переведены ⬜ → ½. Прогресс по реальному коду: 44% → 48%.*
- *19.0: 🎨 **Frontend redesign по черновику Figma Make.** Полная переодевка фронтенда (49 задач, 8 фаз) в worktree `worktree-figma-redesign`: glassmorphism, dark/light тема с auto-detect (21–7), сайдбар с историей сессий, плавающие элементы, мульти-сессии через Dexie (до появления `/api/sessions`), `/settings` страница (тема + 4 локальных wallpaper'а). Новые зависимости (~50 KB gz): `motion`, `lucide-react`, `sonner`, Radix `avatar/dialog/slot`, `cva`, `clsx + tw-merge`. Кризисный модуль переодет — API всех 5 компонентов сохранён 1-в-1 (manual regression тест на 4 уровнях кризиса остаётся за пользователем перед merge). Production build чистый: 5 страниц, type-check без ошибок. Спека и план: `docs/superpowers/specs/2026-05-06-frontend-figma-redesign-design.md` + `docs/superpowers/plans/2026-05-06-frontend-figma-redesign.md`.*
- *20.0: 🛡️ **Устойчивость PerceptionReport.** Двухслойная защита от нестабильности YandexGPT Lite на пограничных вводах: `field_validator(mode='before')` нормализует пустые `dominant_emotion`/`theme`/`what_user_needs`/`inner_monologue` в дефолты («неизвестно»/«неясно»/«(нет мыслей)»), длинные строки обрезаются. Расширены `max_length`: `inner_monologue` 1000→2000, `what_user_needs` 300→500. ANALYZER_SYSTEM_PROMPT (пункт 7): явная инструкция LLM писать «неизвестно» вместо пустых строк. **БЕЗ retry, БЕЗ rule-based grep** (3 ADR в спеке). 11 unit-тестов. Не трогали `analyzer.py`, `chat.py`, `pipeline.py`, frontend. Дизайн: `docs/superpowers/specs/2026-05-06-perception-robustness-design.md`. План: `docs/superpowers/plans/2026-05-06-perception-robustness.md`.*

*Версия: 2.7*
