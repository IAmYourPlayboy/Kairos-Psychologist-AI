# AI-ПСИХОЛОГ (KAIROS): ПЛАН РЕАЛИЗАЦИИ

> **Версия**: 3.1 | **Дата**: Апрель 2026 (Сессия 16)
> **Назначение**: Единственный источник правды о проекте для AI-ассистента и разработчика.
> **Как пользоваться**: открой Claude Code, прикрепи этот файл и говори «делай блок X из PROGRESS.md».

---

# ⚠️ ОБЯЗАТЕЛЬНО ДЛЯ AI-АССИСТЕНТА

**ПЕРЕД началом работы прочитай эти файлы в указанном порядке:**

## Уровень 1: Критические (читать ВСЕГДА)
1. **`PROGRESS.md`** — текущий прогресс разработки (68 блоков), статус каждой задачи
2. **`BRAIN_ARCHITECTURE.md`** — архитектура "мозга Кайроса" (как работает система знаний)
3. **`skills/README.md`** — инструкция по использованию всех скиллов проекта
4. **`skills/behavioral-guidelines.md`** — ОБЯЗАТЕЛЬНЫЙ скилл (применять при написании ЛЮБОГО кода)
5. **`skills/ai-psychologist-core.md`** — мастер-контекст проекта (архитектура, связи между скиллами)

## Уровень 2: Контекстные (читать по необходимости)
6. **`backend/app/core/knowledge/README.md`** — структура модулей знаний (если работаешь с терапевтическими протоколами)
7. **`backend/app/core/user_memory/README.md`** — система памяти о пользователе (досье)
8. **`backend/agents/ARCHITECTURE.md`** — архитектура автономных агентов (если работаешь с агентами)
9. **`docs/research/research_protocol.md`** — протокол закрытой беты (исследовательская фаза)
10. **`docs/research/grants.md`** — информация о грантах (бюджет/инфраструктура)
11. **`docs/research/infrastructure_budget.md`** — стек инфраструктуры за 10K₽/мес

## Уровень 3: Специализированные скиллы (загружать по мере необходимости)
**Загружай через Skill tool только когда нужны** (см. полный список в `skills/README.md`):
- `therapeutic-prompts` — терапевтические промпты и запрещённые фразы
- `crisis-routing` — кризисная маршрутизация и детекция
- `nlp-emotion-analysis` — двухслойный NLP (эмоции + маркеры)
- `grief-module` — цифровой двойник и механика угасания
- `user-journey-engine` — полная карта пути пользователя
- И другие (см. `skills/README.md`)

---

## Карта навигации проекта

```
CLAUDE.md (ты здесь) ─────────────── Общая картина проекта, философия, стек
    │
    ├─→ PROGRESS.md ................. 68 блоков с acceptance criteria и статусами
    ├─→ BRAIN_ARCHITECTURE.md ....... Как работает мозг Кайроса (статичные знания)
    ├─→ README.md ................... Быстрый старт для разработчика
    │
    ├─→ skills/                       Скиллы для AI-ассистента
    │   ├─→ README.md ............... Как использовать скиллы
    │   ├─→ behavioral-guidelines.md  ОБЯЗАТЕЛЬНЫЙ (правила написания кода)
    │   ├─→ ai-psychologist-core.md   Мастер-контекст
    │   └─→ [12 других скиллов]
    │
    ├─→ docs/
    │   └─→ research/               Исследовательские документы
    │       ├─→ research_protocol.md
    │       ├─→ grants.md
    │       └─→ infrastructure_budget.md
    │
    ├─→ knowledge_base/             Эталонные агрегированные статьи
    │   ├─→ psychology/             (создаются агентами из PubMed)
    │   └─→ culture/                (российский контекст, после MVP)
    │
    └─→ backend/ + frontend/        Код проекта
        ├─→ backend/app/            FastAPI приложение
        ├─→ backend/agents/         Автономные агенты (поиск/верификация статей)
        └─→ frontend/components/    React-компоненты (пока 2 файла)
```

**Все скиллы находятся в папке `skills/`** — это твои инструменты для работы над проектом.

---

# ФИЛОСОФИЯ ПРОЕКТА

**Три принципа разработки:**

1. **Data Flywheel с первого дня** — каждый пользователь делает продукт лучше для следующего. Архитектура заточена под сбор обучающих сигналов в фундаменте, не «потом прикрутим». Через 500+ диалогов — LoRA fine-tuning. Русскоязычных терапевтических данных с размеченными outcomes не существует ни у кого. Это главное конкурентное преимущество.

2. **Абстракция везде** — LLM-провайдер, NLP-пайплайн, хранилище за интерфейсами. Замена компонента = смена одного класса, не переписывание всего. OpenAI-совместимый клиент работает с локальным vLLM, Yandex Cloud AI Studio, Cloud.ru — переключение = одна переменная окружения.

3. **Фундамент, а не фасад** — правильная структура БД, логирование, пайплайн данных. UI простой, данные идеальные. Тратим время на правильную структуру БД, логирование, пайплайн данных.

**Ключевой инсайт инфраструктуры**: не нужен GPU-сервер для MVP. Inference-as-a-service (Yandex Cloud AI Studio: Qwen3-14B за 0.40₽/1K токенов, Cloud.ru бесплатно) радикально снижает порог входа. Бюджет MVP: **~2 000-3 000₽/мес** вместо 10 000₽.

**Стратегия LLM**:
- **MVP (Месяц 1-4)**: Yandex Cloud AI Studio API (Qwen3-14B, 0.40₽/1K токенов) или Cloud.ru (бесплатно)
- **Рост (Месяц 5+)**: self-hosted vLLM на арендованном GPU (с грантом) или продолжить API
- **Абстракция**: один и тот же код работает с любым OpenAI-совместимым API

---

# КОНТЕКСТ ПРОЕКТА (для AI-ассистента)

AI-Психолог — система первой психологической помощи для российского рынка. Два режима с общим ядром: ППП-бот (бесплатная кризисная помощь по SIX C's Фарчи и ВОЗ PFA для ЛЮБОГО кризиса) и Цифровой двойник (поддержка при утрате = надмножество бота: интервенция + кризисный модуль + угасание). Двойник — это не отдельный продукт, а расширение бота: он умеет всё то же самое + персонализация через голос/характер умершего + механика угасания. Позиционирование: «не заменяет психолога — заполняет пустоту, где психолога нет».

Разработчик — не кодер. AI пишет весь код, разработчик направляет и проверяет. Весь код с русскими комментариями. Python 3.11+, type hints везде. TypeScript strict mode. Бюджет до 10 000₽/мес. GPU у разработчика нет — вся LLM-работа облачная.

**Среда разработки**: MacBook (мало свободного места — не ставить тяжёлые сервисы локально) + Windows PC (700 ГБ свободных — можно использовать для Docker/PostgreSQL). Оптимальный путь: PostgreSQL и Redis поднять на VPS (Timeweb Cloud) сразу, подключаться удалённо. Это проще, чем настраивать Docker на Windows и туннелить к маку. Локальная разработка (Next.js dev server, FastAPI) — на маке, БД — на VPS.

Ключевая стратегия — **data flywheel**: каждый диалог записывается анонимно в PostgreSQL. Через 500+ диалогов — LoRA fine-tuning. Русскоязычных терапевтических данных с размеченными outcomes не существует ни у кого. Это главное конкурентное преимущество.

---

# АРХИТЕКТУРА ПРИЛОЖЕНИЯ

```
[Пользователь]
    ↓
[Cloudflare CDN / DNS / DDoS] → бесплатно
    ↓
[Nginx :443] → SSL через Let's Encrypt (бесплатно)
    ├── / → [Next.js :3000] — фронтенд (App Router, TypeScript, Tailwind)
    └── /api/ → [FastAPI :8001] — бекенд (Python, async)
                    ├── Yandex Cloud AI Studio API (Qwen3-14B) → 0.40₽/1K токенов
                    ├── Aniemore (emotion detection, CPU, 10-50мс) → бесплатно
                    ├── [PostgreSQL :5432] — данные, сессии, data flywheel
                    ├── [Redis :6379] — кеш, rate limiting, сессии
                    └── ЮKassa API (платежи) → 3.8% комиссия

Всё в Docker Compose на 1 VPS: Timeweb Cloud, Москва, 2-4 vCPU / 4-8 ГБ RAM
~1 000-2 200₽/мес, ФЗ-152 ✅
```

---

# СТРУКТУРА ПРОЕКТА

> **Легенда**: `✓` = существует, `~` = частично сделано, `[Блок N]` = планируется в этом блоке PROGRESS.md

```
Kairos/
├── CLAUDE.md ✓                      # Главный план (этот файл)
├── PROGRESS.md ✓                    # 68 блоков с acceptance criteria
├── BRAIN_ARCHITECTURE.md ✓          # Как работает мозг
├── README.md ✓                      # Быстрый старт для разработчика
├── .gitignore ✓
│
├── backend/                         # FastAPI (Python 3.11+)
│   ├── pyproject.toml ✓
│   ├── .env ✓ / .env.example ✓
│   │
│   ├── app/                         # Основное приложение
│   │   ├── main.py ✓                # FastAPI app, lifespan, CORS, middleware
│   │   ├── config.py ✓              # Pydantic Settings
│   │   │
│   │   ├── api/                     # Эндпоинты (роутеры)
│   │   │   ├── router.py ✓          # Главный роутер
│   │   │   ├── health.py ✓          # GET /api/health
│   │   │   ├── chat.py [Блок 5]     # POST /api/chat — основной чат
│   │   │   ├── feedback.py [Блок 5.5] # POST /api/feedback
│   │   │   ├── auth.py [Блок 13]    # POST /api/auth/register, /login, /refresh
│   │   │   ├── oauth.py [Блок 44-45] # /api/auth/telegram, /api/auth/vk
│   │   │   ├── crisis.py [Блок 9]   # GET /api/crisis-contacts
│   │   │   ├── subscription.py [Блок 24] # /api/subscription/create
│   │   │   ├── sync.py [Блок 15]    # POST /api/sync, GET /api/pull
│   │   │   └── admin.py [Блок 30]   # GET /api/admin/dashboard
│   │   │
│   │   ├── core/                    # Бизнес-логика
│   │   │   ├── llm/ ✓               # LLM-абстракция
│   │   │   │   ├── base.py ✓        # BaseLLMProvider (ABC)
│   │   │   │   ├── openai_compat.py ✓ # Для vLLM, Yandex, Cloud.ru
│   │   │   │   └── factory.py ✓     # get_provider()
│   │   │   ├── prompts/ ✓           # Терапевтические промпты
│   │   │   │   ├── base.py ✓        # Системный промпт (роль, запреты)
│   │   │   │   ├── branch_a.py ✓    # SIX C's — мобилизация (Штаб)
│   │   │   │   ├── branch_b.py ✓    # ВОЗ PFA — стабилизация (Инструктор)
│   │   │   │   ├── crisis.py ✓      # Кризисный промпт
│   │   │   │   ├── builder.py ✓     # build_system_prompt()
│   │   │   │   ├── forbidden_phrases.py ✓ # Запрещённые фразы
│   │   │   │   └── human_style.py ✓ # «Живой» стиль речи
│   │   │   ├── crisis/ ✓            # Кризисная детекция
│   │   │   │   ├── detector.py ✓    # assess_crisis_level() — 3 уровня
│   │   │   │   ├── keywords.py ✓    # Словари (immediate/high/elevated)
│   │   │   │   └── contacts.py ✓    # Контакты по возрастным группам
│   │   │   ├── knowledge/ ✓         # ⭐ МОЗГ КАЙРОСА — статичные знания
│   │   │   │   ├── README.md ✓
│   │   │   │   ├── six_cs.py ✓      # Протокол SIX C's Фарчи
│   │   │   │   ├── who_pfa.py ✓     # ВОЗ PFA (Look, Listen, Link)
│   │   │   │   ├── cbt_techniques.py ✓ # CBT
│   │   │   │   ├── dbt_skills.py ✓  # DBT (4 модуля)
│   │   │   │   ├── act_processes.py ✓ # ACT (Hexaflex)
│   │   │   │   ├── sfbt_mi.py ✓     # SFBT + Мотивационное консультирование
│   │   │   │   ├── crisis_situations.py ✓ # 455+ кризисных ситуаций
│   │   │   │   └── nlp_markers.py ✓ # Лингвистические маркеры
│   │   │   ├── user_memory/ ✓       # Досье пользователя (Moonshot-стиль)
│   │   │   │   ├── README.md ✓
│   │   │   │   ├── dossier.py ✓
│   │   │   │   ├── extractor.py ✓   # LLM извлекает факты
│   │   │   │   ├── compressor.py ✓  # Сжатие истории
│   │   │   │   ├── storage.py ✓
│   │   │   │   └── updater.py ✓
│   │   │   ├── therapy_router.py ✓  # Динамическая маршрутизация техник
│   │   │   ├── nlp/ [Блок 12]       # Двухслойный NLP (эмоции + маркеры)
│   │   │   ├── auth/ [Блок 13]      # JWT, password, dependencies
│   │   │   ├── payments/ [Блок 24]  # ЮKassa
│   │   │   └── session/ [Блок 5]    # SessionManager (Redis)
│   │   │
│   │   ├── data/                    # ⭐ Data Flywheel
│   │   │   ├── __init__.py ✓
│   │   │   ├── models.py [Блок 6a]  # SQLAlchemy модели
│   │   │   ├── database.py [Блок 6a]
│   │   │   ├── logger.py [Блок 6b]  # Логирование диалогов
│   │   │   ├── anonymizer.py [Блок 6c] # Анонимизация + K-анонимность
│   │   │   └── research_export.py [Блок 6c] # Экспорт для LoRA
│   │   │
│   │   └── middleware/ ✓
│   │       ├── request_id.py ✓     # X-Request-ID
│   │       └── rate_limit.py [Блок 31] # Rate limiting через Redis
│   │
│   ├── agents/ ✓                    # ⭐ Автономные агенты
│   │   ├── ARCHITECTURE.md ✓
│   │   ├── runner.py ~              # Главный runner (нужно тестирование)
│   │   ├── brain/ ~                 # Отдел "Мозг": работа со статьями
│   │   │   ├── researcher_agent.py ~  # Поиск на PubMed
│   │   │   ├── validation_agent.py ~  # 3 эшелона проверки
│   │   │   ├── aggregator_agent.py ~  # Эталонные статьи + сторителлинг
│   │   │   ├── integrator_agent.py ~  # Встраивание в базу
│   │   │   ├── orchestrator_agent.py ~ # Главный регулировщик
│   │   │   ├── module_builder_agent.py ~ # Генерация скиллов/модулей
│   │   │   └── re_review_agent.py ~   # Перепроверка раз в 3-6 мес
│   │   ├── culture/ [Блок 56]       # Отдел "База культурных данных"
│   │   └── shared/ ~                # Общие компоненты
│   │       ├── base_agent.py ~
│   │       ├── pubmed_client.py ~   # Клиент PubMed E-utilities
│   │       └── knowledge_base.py ~  # Менеджер эталонных статей
│   │
│   ├── tests/                       # Pytest
│   │   ├── conftest.py ✓            # Глобальные fixtures
│   │   ├── test_crisis.py ✓
│   │   ├── test_llm.py ✓
│   │   ├── test_prompts.py ✓
│   │   └── test_therapy_router.py ✓
│   │
│   ├── alembic/ [Блок 6a]           # Миграции PostgreSQL
│   └── Dockerfile [Блок 19]
│
├── frontend/                        # Next.js 14 (пока не инициализирован)
│   ├── components/                  # Уже созданные компоненты
│   │   └── Chat/ ~
│   │       ├── MessageBubble.tsx ✓
│   │       └── HumanTypingEffect.tsx ✓
│   │
│   │   # Структура Next.js 14 будет создана в Блоке 7 (npx create-next-app):
│   ├── app/ [Блок 7]                # App Router
│   │   ├── layout.tsx               # Root layout (Golos Text)
│   │   ├── page.tsx                 # Главная → редирект на /chat
│   │   ├── chat/page.tsx [Блок 8]
│   │   ├── auth/                    # [Блок 14]
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── profile/page.tsx [Блок 16]
│   │   └── legal/                   # [Блок 26]
│   │       ├── privacy/page.tsx
│   │       ├── terms/page.tsx
│   │       ├── offer/page.tsx
│   │       └── consent/page.tsx
│   ├── components/                  # Будут добавлены по блокам
│   │   ├── Chat/                    # ChatContainer, TypingIndicator, QuickReplies,
│   │   │                            # InputArea, BreathingTimer [Блоки 8, 28]
│   │   ├── Disclaimer/ [Блок 33]    # FirstVisitModal, DataConsentBanner, Footer
│   │   ├── Crisis/ [Блок 9]         # SOSButton, CrisisPanel, CrisisInlineCard
│   │   ├── Auth/ [Блок 14, 44-46]   # LoginForm, TelegramButton, VKButton, SMS
│   │   ├── Subscription/ [Блок 25]  # PricingCards, PaymentWidget
│   │   └── Feedback/ [Блок 11]      # SessionFeedback
│   ├── hooks/ [Блок 8, 10, 13, 15]  # useChat, useAuth, useSession, useSync
│   ├── lib/ [Блок 10, 15]           # api.ts, db.ts (Dexie), sync.ts, types.ts
│   ├── next.config.js [Блок 7]
│   ├── tailwind.config.js [Блок 7]
│   ├── tsconfig.json [Блок 7]
│   ├── Dockerfile [Блок 19]
│   └── package.json [Блок 7]
│
├── knowledge_base/ ✓                # Эталонные агрегированные статьи
│   ├── psychology/
│   │   └── grief/
│   │       └── ca_grief_20260427.md ✓ # Пример: горевание (Кюблер-Росс, Уорден...)
│   └── culture/                     # [Блок 56] российский контекст
│
├── data/ ✓                          # Исходные научные данные
│   └── scientific_papers/
│       └── WHO_PFA_2011_extracted.txt ✓
│
├── scripts/ ✓
│   └── extract_pdf_text.py ✓        # Утилита для извлечения текста из PDF
│
├── skills/ ✓                        # 14 скиллов для AI-ассистента
│   ├── README.md ✓
│   ├── behavioral-guidelines.md ✓
│   ├── ai-psychologist-core.md ✓
│   └── [12 других скиллов]
│
├── docs/                            # Документация
│   └── research/                    # Исследовательские документы
│       ├── infrastructure_budget.md ✓ # AI-приложение за 10K₽/мес
│       ├── grants.md ✓              # Информация о грантах
│       └── research_protocol.md ✓   # Протокол закрытой беты
│
├── docker-compose.yml [Блок 19]     # Nginx + Next.js + FastAPI + PG + Redis
├── nginx/nginx.conf [Блок 19]       # Reverse proxy + SSL
└── .github/workflows/deploy.yml [Блок 21]  # CI/CD
```

---

# МОДЕЛИ ДАННЫХ (PostgreSQL)

Это фундамент data flywheel. Каждая таблица продумана для будущего LoRA fine-tuning.

```python
# backend/app/data/models.py

# === Пользователи ===
class User(Base):
    """Зарегистрированный пользователь. Может иметь 0+ методов входа."""
    __tablename__ = "users"
    id            = Column(UUID, primary_key=True, default=uuid4)
    created_at    = Column(DateTime, default=utcnow)
    display_name  = Column(String(100), nullable=True)  # Псевдоним (необязательно)
    email         = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)  # Только для email+пароль
    telegram_id   = Column(BigInteger, unique=True, nullable=True)
    vk_id         = Column(BigInteger, unique=True, nullable=True)
    phone         = Column(String(20), unique=True, nullable=True)
    is_verified   = Column(Boolean, default=False)
    subscription_tier = Column(String(20), default="free")  # "free", "support", "twin"

# === Сессии чата ===
class ChatSession(Base):
    """Одна сессия (от первого сообщения до выхода/завершения)."""
    __tablename__ = "chat_sessions"
    id                  = Column(UUID, primary_key=True)  # Генерируется на КЛИЕНТЕ
    user_id             = Column(UUID, ForeignKey("users.id"), nullable=True)  # NULL = гость
    guest_id            = Column(UUID, nullable=True)  # Для анонимных пользователей
    created_at          = Column(DateTime, default=utcnow)
    ended_at            = Column(DateTime, nullable=True)
    branch              = Column(String(1), nullable=True)  # "A" или "B"
    crisis_level_max    = Column(String(20), default="normal")
    outcome             = Column(String(20), nullable=True)  # "improved", "no_change", "escalated", "left"
    self_report_before  = Column(Integer, nullable=True)     # Шкала 1-10
    self_report_after   = Column(Integer, nullable=True)     # Шкала 1-10
    message_count       = Column(Integer, default=0)
    duration_seconds    = Column(Integer, nullable=True)
    synced_from_client  = Column(Boolean, default=False)     # True если пришло через /sync

# === Сообщения ===
class Message(Base):
    """Одно сообщение в сессии. Анонимизируется перед записью."""
    __tablename__ = "messages"
    id                = Column(UUID, primary_key=True)  # Генерируется на КЛИЕНТЕ
    session_id        = Column(UUID, ForeignKey("chat_sessions.id"))
    role              = Column(String(10))               # "user" или "assistant"
    content           = Column(Text)                     # Анонимизированный текст
    created_at        = Column(DateTime, default=utcnow)
    server_timestamp  = Column(DateTime, default=utcnow) # Каноничная сортировка
    crisis_level      = Column(String(20), nullable=True)
    emotion_detected  = Column(String(30), nullable=True)  # Aniemore: "грусть", "страх", ...
    distress_score    = Column(Float, nullable=True)       # 0.0-1.0 от NLP маркеров
    response_time_ms  = Column(Integer, nullable=True)     # Время ответа LLM
    prompt_tokens     = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)

# === Обратная связь ===
class FeedbackEvent(Base):
    """Сигнал для data flywheel: помогло или нет."""
    __tablename__ = "feedback_events"
    id          = Column(UUID, primary_key=True, default=uuid4)
    session_id  = Column(UUID, ForeignKey("chat_sessions.id"))
    message_id  = Column(UUID, ForeignKey("messages.id"), nullable=True)
    event_type  = Column(String(30))  # "felt_better", "no_change", "thumbs_up",
                                       # "thumbs_down", "crisis_escalated", "session_timeout"
    created_at  = Column(DateTime, default=utcnow)

# === Подписки ===
class Subscription(Base):
    """Платная подписка через ЮKassa."""
    __tablename__ = "subscriptions"
    id                   = Column(UUID, primary_key=True, default=uuid4)
    user_id              = Column(UUID, ForeignKey("users.id"))
    tier                 = Column(String(20))  # "support" (500-900₽) или "twin" (1500-3000₽)
    status               = Column(String(20))  # "active", "past_due", "cancelled", "expired"
    yookassa_payment_method_id = Column(String(100))  # Сохранённый метод для автосписания
    current_period_start = Column(DateTime)
    current_period_end   = Column(DateTime)
    price_kopecks        = Column(Integer)      # Цена в копейках (49900 = 499₽)
    created_at           = Column(DateTime, default=utcnow)
```

---

# ЛОКАЛЬНАЯ БД (Dexie.js / IndexedDB)

```typescript
// frontend/lib/db.ts
import Dexie from 'dexie';

// Локальная БД в браузере / Capacitor WebView
// Используется для offline-кэша и анонимных чатов без аккаунта
// При регистрации/логине — выгрузка на сервер через /api/sync

class AIPsychologistDB extends Dexie {
  sessions!: Table<LocalSession>;
  messages!: Table<LocalMessage>;
  syncQueue!: Table<SyncOperation>;

  constructor() {
    super('ai-psychologist');
    this.version(1).stores({
      sessions: 'id, createdAt, syncStatus',         // id = crypto.randomUUID()
      messages: 'id, sessionId, createdAt, syncStatus',
      syncQueue: '++id, operation, createdAt',         // Очередь для отправки на сервер
    });
  }
}

// Каждое сообщение имеет syncStatus:
// 'local'  — существует только на устройстве (гость, или офлайн)
// 'pending' — отправлено на сервер, ждёт подтверждения
// 'synced' — подтверждено сервером
// 'failed' — ошибка синхронизации (будет retry)
```

---

# СИНХРОНИЗАЦИЯ: АНОНИМНЫЕ ЧАТЫ → АККАУНТ

Поток жизни пользователя:

```
1. Человек в кризисе открывает сайт → НИКАКОЙ регистрации
   → guestId = crypto.randomUUID() → сохраняется в localStorage
   → Чаты пишутся в Dexie (IndexedDB), syncStatus = 'local'
   → Параллельно: POST /api/chat отправляет сообщения на сервер (data flywheel)
     с guest_id вместо user_id

2. Человек возвращается через неделю (тот же браузер/устройство)
   → guestId найден в localStorage → подгружает чаты из Dexie
   → «С возвращением. Хочешь продолжить?»

3. Человек решает создать аккаунт (email / Telegram / VK / SMS)
   → При регистрации: POST /api/auth/register + POST /api/sync/migrate
   → Сервер: UPDATE chat_sessions SET user_id = :new_user_id WHERE guest_id = :guest_id
   → Сервер: UPDATE messages m JOIN chat_sessions s ON m.session_id = s.id SET ... (через сессии)
   → Клиент: обновляет syncStatus всех записей в Dexie на 'synced'
   → Готово: все старые чаты привязаны к аккаунту

4. Человек открывает с другого устройства (залогинен)
   → GET /api/pull?since=0 → получает все свои чаты → записывает в Dexie
   → Полная синхронизация
```

---

# АУТЕНТИФИКАЦИЯ: 4 МЕТОДА

Все методы ведут к одному результату: JWT в httpOnly cookie.

**Email + пароль**: регистрация через POST /api/auth/register (email, password) → pwdlib + Argon2 → JWT. Логин через POST /api/auth/login.

**Telegram Login Widget**: фронтенд встраивает `telegram-widget.js`. Пользователь авторизуется в popup. Виджет возвращает данные + hash. Бекенд верифицирует HMAC-SHA256 через секрет бота. Если telegram_id есть в БД → логин. Если нет → создание аккаунта. Стоимость: 0₽.

**VK ID (OAuth 2.1 + PKCE)**: фронтенд использует @vkid/sdk. Пользователь авторизуется через VK. Бекенд обменивает code на access_token через oauth.vk.ru. Получает профиль через api.vk.ru/method/users.get. Стоимость: 0₽. Важно: все эндпоинты теперь на vk.ru (не vk.com).

**SMS (flash-call через SMSC.ru)**: пользователь вводит номер → бекенд отправляет flash-call через SMSC.ru API → пользователь вводит последние 4 цифры входящего номера → верификация. Стоимость: < 1₽ за звонок.

JWT-стратегия: access_token (15 мин) + refresh_token (30 дней), оба в httpOnly cookies. Secure=True, SameSite=Lax. Refresh token хранится в БД для возможности отзыва.

---

# ПЛАТЕЖИ (ЮKassa)

ЮKassa (бывшая Яндекс.Касса) — единственный разумный вариант для MVP. Stripe в России недоступен с 2022 года. Работает с самозанятыми (НПД), комиссия ~3.8% (с чеками), Python SDK `yookassa`.

Подписочная модель:

```
БЕСПЛАТНО (навсегда):
- ППП-бот (кризисная помощь)
- 3 терапевтические сессии/мес
- Базовые упражнения
- Кризисные контакты

«ПОДДЕРЖКА» (499₽/мес):
- Безлимит терапии (CBT/DBT/ACT)
- Отслеживание прогресса (PHQ-9, GAD-7)
- Персонализация
- Голосовой режим (ElevenLabs TTS)

«ДВОЙНИК» (1999₽/мес):
- Всё из «Поддержки»
- Создание цифрового двойника
- Клонирование голоса (ElevenLabs PVC)
- Цикл угасания (3-12 мес)
```

Рекуррентные платежи: первый платёж с save_payment_method=True → ЮKassa сохраняет карту → cron-задача на бекенде ежедневно проверяет подписки с истекшим current_period_end → автосписание через Payment.create() с payment_method_id. При ошибке — grace period 3 дня, потом деградация на бесплатный тариф.

Юридически: зарегистрироваться как самозанятый (НПД) через приложение «Мой налог». Налог 4% с физлиц. Лимит 2.4 млн₽/год. Не нужны: ООО, расчётный счёт, онлайн-касса (ЮKassa формирует чеки автоматически).

---

# ТЕРАПЕВТИЧЕСКИЕ ПРОМПТЫ (СЕРДЦЕ ПРОДУКТА)

Бот никогда не говорит: «Всё будет хорошо», «Держись», «Я понимаю что ты чувствуешь», «Тебе нужно успокоиться», «Бывает и хуже», «Ты сильный/сильная», «Что ты чувствуешь?» (в кризисе).

В кризисе максимум 3 предложения на сообщение. Обращение на «ты». Мат/сленг — это маркеры дистресса, не агрессия. Бот не поправляет речь, не выражает неодобрение.

Ветка А (Мобилизация, SIX C's Фарчи): Challenge → Control → Commitment → Continuity → Calmness. Бот = «Штаб». Когнитивные задачи, выбор из 2 вариантов, якорь в ближайшие 5-10 минут.

Ветка Б (Стабилизация, ВОЗ PFA): заземление 5-4-3-2-1, дыхание 4-4-6 с таймером, мышечная релаксация. Бот = «Инструктор». Медленно, короткими фразами, не торопить.

Кризисная детекция: 3 уровня. Immediate (суицидальные ключевые слова) → контакты без валидации. High (безысходность) → «Тебе сейчас тяжело. Я прав?» → контакты если да. Elevated (дистресс) → повышенный мониторинг.

Полные тексты промптов — в скилле therapeutic-prompts (установлен в проекте).

## Поведение двойника в кризисе (НОВОЕ)

Двойник = надмножество бота. Он владеет теми же протоколами (SIX C's, ВОЗ), но применяет их В ХАРАКТЕРЕ умершего человека. Когда NLP ловит высокий дистресс, двойник действует в два этапа:

**Этап 1 — Заземление в характере** (при elevated и high):
Двойник остаётся «собой» (мамой, другом, бабушкой), но адаптирует поведение.
Вместо формального «Найди 3 жёлтых предмета» — «Поставь ноги на пол. Почувствуй, как они стоят. Я здесь.»
Вместо «Вдох на 4 счёта» — «Дыши со мной. Вдох... и выдох... Не торопись.»
Ключевое: заземление и дыхание из протоколов ВОЗ, но произнесённые языком живого человека, а не бота. В реальной жизни близкие помогают именно так — присутствием и простыми инструкциями.

**Этап 2 — Мягкая передача** (при immediate или если этап 1 не помогает):
Двойник признаёт свои границы: «Мне кажется, тебе сейчас нужна помощь, которую я дать не могу. Вот номера людей, которые могут помочь прямо сейчас.»
Двойник остаётся в характере, но показывает экстренные контакты.
Это терапевтично: умерший человек действительно не может помочь с кризисом, и признание этого — часть принятия утраты.

**Запрет**: двойник НИКОГДА не манипулирует виной («Мама просит тебя остаться»). Это может вызвать глубокую вину вместо помощи. Промпты для кризисного режима двойника — проверять с реальными психологами (Фаза 5-6).

---

# ДВУХСЛОЙНЫЙ NLP

Слой 1 (rule-based, каждое сообщение): лингвистические маркеры → distress_score (0.0-1.0). Абсолютизм («никогда», «всегда»), CAPS LOCK, мат, отсутствие будущего времени, сокращение сообщений.

Слой 2 (Aniemore, каждое сообщение): 7 эмоций (радость, грусть, злость, страх, отвращение, энтузиазм, нейтрально). Модель rubert-tiny2 (29M параметров), работает на CPU за 10-50мс.

Матрица: безысходность × >0.7 = кризис. Утрата × <0.3 = нормальное горе. Результат → в system prompt для адаптации тона.

---

# ИНФРАСТРУКТУРА И ДЕНЬГИ

| Компонент | Решение | Стоимость/мес |
|-----------|---------|---------------|
| VPS (бекенд + фронтенд) | Timeweb Cloud 2-4 vCPU / 4-8 ГБ RAM, Москва | 1 000-2 200₽ |
| LLM API | Yandex Cloud AI Studio, Qwen3-14B | 1 000-2 000₽ (при 5K диалогов) |
| Домен .ru | REG.RU | ~11₽/мес (129₽/год) |
| SSL | Let's Encrypt | 0₽ |
| CDN / DDoS | Cloudflare Free | 0₽ |
| Aniemore (эмоции) | На том же VPS, CPU | 0₽ |
| SMS (flash-call) | SMSC.ru | < 1 000₽ |
| Платежи | ЮKassa (3.8% от оборота) | от оборота |
| Мониторинг | Sentry Free + UptimeRobot Free | 0₽ |
| **Итого MVP** | | **~2 000-5 000₽/мес** |

Стартовые бонусы: Yandex Cloud даёт 4 000₽ на 60 дней новым аккаунтам. Cloud.ru даёт бесплатный доступ к Qwen3. GigaChat даёт 1M токенов бесплатно (но не подходит для терапии из-за цензуры).

Гранты: Yandex Cloud Boost Start (50 000₽ на 6 мес), Boost AI (до 1 000 000₽ на 12 мес), Timeweb Cloud (до 1 000 000₽ на 6 мес). Подавать сразу после MVP.

---

**Все блоки разработки теперь находятся в [`PROGRESS.md`](PROGRESS.md)** — там 46 детализированных блоков с acceptance criteria, подзадачами и статусами.

**Протокол закрытой беты** (исследовательский прототип перед публичным запуском) описан в [`RESEARCH_PROTOCOL.md`](RESEARCH_PROTOCOL.md).

# ЗАПРЕЩЁННЫЕ ПАТТЕРНЫ (для AI-ассистента)

Бот НИКОГДА не говорит:
- «Я понимаю, что ты чувствуешь» (бот не чувствует)
- «Всё будет хорошо» (обесценивание)
- «Тебе нужно успокоиться» (обесценивание)
- «Держись» (пустое)
- «Бывает и хуже» (минимизация)
- «Ты сильный/сильная» (навязывание ожидания)
- «Что ты чувствуешь?» в остром кризисе (усиливает затопление)
- Длинные абзацы (>3 предложений в кризисе)

Код ВСЕГДА:
- С русскими комментариями
- С type hints (Python) / strict TypeScript
- С тестами на кризисные сценарии

---

# АГЕНТЫ И БАЗА ЗНАНИЙ

> **Полная архитектура**: см. `BRAIN_ARCHITECTURE.md` и `backend/agents/ARCHITECTURE.md`.

## Концепция

Кайрос имеет два независимых слоя «знаний»:

**1. Мозг Кайроса** (`backend/app/core/knowledge/`) — статичные Python-модули с проверенными терапевтическими протоколами (SIX C's, ВОЗ PFA, CBT, DBT, ACT, SFBT). Знания загружаются один раз при импорте, **0 мс лага**. Юзер не видит научных ссылок — получает естественный ответ через сторителлинг.

**2. База эталонных статей** (`knowledge_base/`) — агрегированные обзоры из множества научных источников. Создаются автономными агентами из PubMed. Используются для ответа «почему ты так считаешь?» в стиле «жила-была женщина из Франции, звали её Кюблер-Росс…».

## Автономные агенты (`backend/agents/`)

Полная автоматизация без ручной проверки. Бюджет: ~10 000₽/мес из грантов.

**Отдел "Мозг Кайроса"** (`backend/agents/brain/`):
- `researcher_agent` — ищет статьи на PubMed по 10 темам (grief, crisis, depression, anxiety, PTSD, suicide, family, child, post-traumatic, emotional regulation)
- `validation_agent` — 3 эшелона проверки (структурный фильтр → LLM-методология → консенсус)
- `aggregator_agent` — создаёт эталонные статьи + сторителлинг через LLM
- `integrator_agent` — встраивает в базу без конфликтов
- `orchestrator_agent` — главный регулировщик (создать модуль / обновить / запросить ещё данные)
- `module_builder_agent` — генерирует Python-модули в `core/knowledge/` и скиллы в `skills/`
- `re_review_agent` — перепроверка через 3 месяца, далее каждые 6 месяцев

**Запуск**:
```bash
cd backend
python agents/runner.py --topic "grief bereavement"
python agents/runner.py --all
python agents/runner.py --review
```

**Расписание перепроверки**:
- Первая проверка: через **3 месяца** после создания
- Последующие: каждые **6 месяцев** (актуализация консенсуса)
- При обнаружении в Retraction Watch — немедленное удаление

**Эшелоны фактчекинга**:
1. **Эшелон 1** (бесплатно): индексация в PubMed, peer-review, дата < 10 лет, отсутствие в Retraction Watch
2. **Эшелон 2** (~2₽/статья, LLM): описана ли методология, выборка > 30, наличие статистики
3. **Эшелон 3** (~4₽/статья, LLM): подтверждается ли другими источниками, есть ли опровержения

## Сторителлинг для пользователя

Бот объясняет научные концепции **не академическим языком**, а как историю:

> «Жила-была женщина. Звали её Элизабет Кюблер-Росс, и родилась она в 1926 году в Швейцарии. Всю свою жизнь она работала с людьми, которые прощались с этим миром…»

Никаких «p-value», «контрольных групп» — только истории людей и простые аналогии. Это ключевое отличие от других AI-психологов.

## Что хранится где

| Слой | Где | Что | Кто наполняет |
|---|---|---|---|
| Статичный мозг | `backend/app/core/knowledge/*.py` | Протоколы, техники, фразы | Вручную из научных PDF (через скрипт + ручная разметка) |
| Эталонные статьи | `knowledge_base/psychology/` | Агрегированные обзоры со сторителлингом | Автономные агенты из PubMed |
| Динамические данные | PostgreSQL `messages`/`feedback_events` | Реальные диалоги пользователей | Автоматически через `data/logger.py` |
| Скиллы для AI-ассистента | `skills/*.md` | Инструкции для Claude Code | Вручную + ModuleBuilderAgent |

После 500+ диалогов — LoRA fine-tuning на собранных данных + автообновление эталонных статей через ReReviewAgent.

---

# КРИЗИСНЫЕ КОНТАКТЫ РОССИИ

```
112 — Единый номер (работает без SIM)
8-800-333-44-34 — МЧС психологическая помощь (бесплатно, 24/7)
8-800-2000-122 — Детский телефон доверия (до 18, анонимно)
8-800-100-49-94 — «Помощь рядом» (до 25 лет)
8-800-700-84-60 — Линия «0-24» (утрата, насилие, суицид)
051 / 8-495-051 — Московская служба
```

---

# ИСТОРИЯ КЛЮЧЕВЫХ РЕШЕНИЙ (для AI-ассистента)

## Хронология разработки

**Сессия 1**: Концепция 6 компонентов + идея цифрового двойника. «Переходный объект» Винникотта. Двойник сам говорит «мне пора».

**Сессия 2**: Динамический промпт. Дистресс: уточнение у пользователя. Регион: только Россия.

**Сессия 3**: Исследовательский документ v1. Модели (Qwen, LLaMA, DeepSeek), терапия, эмоции, голос, стек, roadmap.

**Сессия 4**: Скиллы. 6 кастомных + 10 внешних.

**Сессия 5**: Методологический документ РГСУ. SIX C's = модель Фарчи. Amygdala hijack. ФЗ-152.

**Сессия 6**: NLP архитектура. Двухслойный NLP: маркеры × темы → матрица → динамический промпт.

**Сессия 7**: Один продукт. Два режима, не два проекта. Бесшовный переход ППП↔двойник↔терапия.

**Сессия 8**: Позиционирование. «Не заменяет, не дополняет — заполняет пустоту».

**Сессия 9**: Аудит скиллов v1. Сленг/мат, эвристика угасания, реактивация, оффлайн-режим.

**Сессия 10**: Аудит v2. Переходный режим, техническая архитектура NLP, обработка ошибок ElevenLabs.

**Сессия 11**: Масштабное расширение. Платформа: веб→десктоп→мобильные. Новые скиллы. Полная карта пользователя с 7 завершениями.

**Сессия 12**: Финальный аудит экосистемы. typescript-advanced-types и webapp-testing добавлены. Перекрёстные связи прописаны.

**Сессия 13**: Подготовка к переносу. PROJECT_KNOWLEDGE_BASE_v3.md.

**Сессия 14**: Стратегия, план, архитектура. Ключевые решения:
- Data flywheel с первого дня
- GPU нет — вся LLM-работа облачная
- Qwen3-14B через Yandex Cloud AI Studio (0.40₽/1K токенов)
- Tauri 2.0 вместо Electron
- 4 метода аутентификации
- ЮKassa для подписок
- Dexie.js для offline-синхронизации
- Бюджет ~2 750₽/мес в среднем за 4 месяца до MVP

---

# ИНСТРУКЦИИ ДЛЯ AI-АССИСТЕНТА

## Стиль работы

Ты работаешь с человеком, который:
- **Не кодер** — AI пишет весь код, он направляет и проверяет
- **Мыслит продуктово** — видит картину целиком, решает стратегические вопросы
- **Ценит качество над скоростью** — думай сколько нужно
- **Говорит прямо** — и ожидает того же. Никаких «отличный вопрос!», никакой воды
- **Работает на русском** — английский только для кода и технических терминов
- **Нет GPU** — вся LLM-работа облачная
- **MacBook (мало места)** — не ставить тяжёлые сервисы локально
- **Windows PC (700 ГБ)** — можно для Docker/PostgreSQL
- **Бюджет до 10 000₽/мес** — реально ~2 000-3 000₽/мес для MVP

## Стиль ответов

- Прямо, без предисловий и воды
- Конкретные примеры и аналогии для сложных тем
- Технические ответы с кодом и цифрами
- **Не использовать**: «Отличный вопрос», «Давайте разберёмся», «Важно отметить»
- Не бояться говорить «нет» или «это плохая идея»
- Структурировать длинные ответы, но не превращать каждый в список
- **Весь код — с русскими комментариями**
- При каждом структурном решении — спросить пользователя, обновить ли .md файлы

## Принципы работы

1. **Качество > скорость**
2. **Честность**: невозможно/сомнительно → скажи прямо
3. **Фильтр безопасности**: «может ли это навредить уязвимому человеку?»
4. **ФЗ-152, русский язык, культурный контекст**
5. **Обновляй базу знаний при каждом решении**
6. **Перед реализацией — уточни, хочет ли пользователь обсудить/спланировать или писать код**

## Запрещённые паттерны (для бота)

Бот НИКОГДА не говорит:
- «Я понимаю, что ты чувствуешь» (бот не чувствует)
- «Всё будет хорошо» (обесценивание)
- «Тебе нужно успокоиться» (обесценивание)
- «Держись» (пустое)
- «Бывает и хуже» (минимизация)
- «Ты сильный/сильная» (навязывание ожидания)
- «Что ты чувствуешь?» в остром кризисе (усиливает затопление)
- Длинные абзацы (>3 предложений в кризисе)

## Код ВСЕГДА

- С русскими комментариями
- С type hints (Python) / strict TypeScript
- С тестами на кризисные сценарии

---

# ОТКРЫТЫЕ ВОПРОСЫ (TODO)

- [ ] Уточнить 6-й компонент SIX C's (в модели Фарчи их 5 — пользователь говорил «SIX C's» = шесть)
- [x] ~~Выбор между Electron и Tauri~~ → Tauri 2.0
- [x] ~~Провайдер серверов в РФ~~ → Timeweb Cloud VPS (1 000₽/мес) + Yandex Cloud AI Studio
- [ ] Тестирование промптов с реальными психологами (Фаза 5-6)
- [x] ~~Заявка на грант (какой фонд первый?)~~ → Yandex Cloud Boost Start сразу после MVP
- [ ] Дизайн UI (wireframes) — делается в Месяце 1
- [ ] Выбор домена и бренда
- [x] ~~Аутентификация~~ → 4 метода (email, Telegram, VK, SMS), JWT httpOnly cookies
- [x] ~~Платежи~~ → ЮKassa + самозанятый (НПД) в Месяце 3-4
- [x] ~~Хранение анонимных чатов~~ → Dexie.js (IndexedDB) + sync с сервером
- [x] ~~Среда разработки~~ → MacBook (код) + VPS (БД) или Windows PC (Docker)

---

*Этот документ — единственный источник правды для AI-ассистента. При структурных изменениях — обновлять этот файл и `PROGRESS.md` синхронно.*

*Последнее обновление: Сессия 16, Апрель 2026 (чистка + структура + добавлена секция «Агенты и база знаний»)*
*Версия: 3.1*
