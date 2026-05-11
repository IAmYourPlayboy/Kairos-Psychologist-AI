# Kairos / AI-Психолог

> Сервис первой психологической помощи для российского рынка.
> «Не заменяет психолога — заполняет пустоту, где психолога нет рядом».

---

## 🚀 Быстрый старт

### Для AI-ассистента (Claude Code и др.)

Прочти в этом порядке:

1. **`CLAUDE.md`** — главный план проекта (архитектура, стек, философия)
2. **`PROGRESS.md`** — что сделано, что в работе, что дальше
3. **`BRAIN_ARCHITECTURE.md`** — как устроен «мозг» (база знаний)
4. **`skills/README.md`** — как использовать скиллы проекта
5. **`skills/behavioral-guidelines.md`** — обязательные правила написания кода

### Для разработчика

**Сервисы-зависимости** (Redis — нужен для слоя восприятия: Mood + очередь ReflectionAgent):

```bash
# Из корня репозитория (требуется Docker Desktop)
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml ps          # должен быть healthy
```

Без Redis `/api/chat` будет падать в fallback на каждом сообщении («Извини, я сейчас не могу отвечать»). PostgreSQL для dev пока не нужен — используется SQLite из коробки.

**Backend (FastAPI):**

```bash
cd backend
python -m venv venv
venv\Scripts\activate                  # Windows (PowerShell: venv\Scripts\Activate.ps1)
# source venv/bin/activate              # Mac/Linux
pip install -e .

# Запуск dev-сервера
uvicorn app.main:app --reload --port 8001

# Проверка
curl http://localhost:8001/api/health
```

**Frontend (Next.js 16):**

```bash
cd frontend
npm install
npm run dev                             # http://localhost:3000

# Если Turbopack падает с "Файл подкачки слишком мал" (Windows + мало virtual memory):
npx next dev --webpack                  # временно использовать webpack-бандлер
```

**Celery worker (ReflectionAgent):**

ReflectionAgent извлекает факты в Dossier через 15 минут (или `REFLECTION_DELAY_SECONDS` из `.env`) после последнего сообщения. Без запущенного worker'а досье не наполняется — бот не будет помнить пользователя между сессиями.

**Важно:** worker должен слушать очередь `reflection` (не только `default`). В `celery_app.py` задача `run_reflection` маршрутизируется в очередь `reflection` через `task_routes`.

```bash
cd backend
venv\Scripts\activate

# Правильная команда (Windows + Linux):
celery -A app.celery_app worker --loglevel=info --pool=solo -Q reflection,default

# Флаги:
#   --pool=solo        обязателен на Windows (иначе Celery падает на форке процессов)
#   -Q reflection,default   слушать обе очереди; без -Q reflection задачи зависнут в Redis
```

При старте должна появиться строка:
```
[tasks]
  . app.core.perception.reflection_tasks.run_reflection
...
.> reflection         exchange=reflection(direct) key=reflection
```

Если в выводе **только** `default` — флаг `-Q` был забыт, задачи не выполнятся.

**Dev-скрипты с кириллическими данными на Windows:**

При запуске Python-скриптов, которые печатают русский текст (например, просмотр Dossier), нужен явный UTF-8 вывод — иначе `UnicodeEncodeError: 'charmap' codec can't encode`:

```bash
# Windows (PowerShell/cmd):
PYTHONIOENCODING=utf-8 venv\Scripts\python.exe script.py
# или внутри скрипта:
#   sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

На Linux/Mac это не нужно — терминал по умолчанию UTF-8.

---

## 📁 Структура проекта

```
Kairos/
├── CLAUDE.md                # Главный план для AI-ассистента
├── PROGRESS.md              # Чеклист задач (68 блоков)
├── BRAIN_ARCHITECTURE.md    # Как работает мозг Кайроса
├── README.md                # Этот файл
│
├── backend/                 # FastAPI бекенд
│   ├── app/                 # Основное приложение
│   │   ├── api/             # Эндпоинты
│   │   ├── core/            # Бизнес-логика
│   │   │   ├── crisis/      # Кризисная детекция
│   │   │   ├── llm/         # LLM-абстракция
│   │   │   ├── prompts/     # Терапевтические промпты
│   │   │   ├── knowledge/   # Мозг Кайроса (статичные знания)
│   │   │   └── user_memory/ # Досье пользователя
│   │   ├── data/            # Модели данных, БД
│   │   └── middleware/      # Middleware (request_id, CORS)
│   ├── agents/              # Автономные агенты (поиск/верификация статей)
│   │   ├── brain/           # Агенты работы с научными статьями
│   │   ├── culture/         # Агенты работы с культурными данными
│   │   └── shared/          # Общие компоненты (PubMed, knowledge_base)
│   └── tests/               # Pytest-тесты
│
├── frontend/                # Next.js фронтенд (в разработке)
│   └── components/Chat/     # Чат-компоненты
│
├── skills/                  # Скиллы для AI-ассистента
├── knowledge_base/          # Эталонные агрегированные статьи
│   ├── psychology/          # По психологии
│   └── culture/             # По культурному контексту
│
├── data/                    # Исходные научные данные
│   └── scientific_papers/   # PDF и извлечённые тексты
│
├── scripts/                 # Утилиты (extract_pdf_text.py)
│
└── docs/                    # Документация
    └── research/            # Исследовательские документы
        ├── infrastructure_budget.md   # AI-приложение за 10K₽/мес
        ├── grants.md                  # Информация о грантах
        └── research_protocol.md       # Протокол закрытой беты
```

---

## 🎯 Текущий статус

**Фаза**: Фундамент (Месяц 1 из 4 до MVP)
**Прогресс**: см. [PROGRESS.md](PROGRESS.md)

### Что уже работает
- ✅ FastAPI каркас с `/api/health`
- ✅ LLM-абстракция (OpenAI-совместимый клиент)
- ✅ Промпты SIX C's и ВОЗ PFA
- ✅ Кризисная детекция (3 уровня)
- ✅ База знаний: ВОЗ, SIX C's, CBT, DBT, ACT, SFBT
- ✅ Архитектура автономных агентов (Researcher → Validator → Aggregator → ...)

### Что в работе
- 🔄 `/api/chat` — главный эндпоинт (Блок 5)
- 🔄 Модели данных и PostgreSQL (Блок 6a)
- 🔄 Next.js фронтенд (Блок 7)

---

## 🛠️ Технический стек

| Слой | Технология | Назначение |
|---|---|---|
| LLM | Qwen3-14B через Yandex Cloud AI Studio | Основной разговор |
| Backend | FastAPI (Python 3.11+) | API, бизнес-логика |
| Frontend | Next.js 14 + TypeScript + Tailwind | UI |
| БД | PostgreSQL 16 + Redis 7 | Данные + кэш |
| Локально | Dexie.js (IndexedDB) | Offline-first |
| Платежи | ЮKassa | Подписки |
| NLP | Aniemore (CPU) | Эмоции |
| Хостинг | Timeweb Cloud (Москва) | ФЗ-152 |

---

## 📜 Лицензия и юридический статус

- Юрлицо: самозанятый (НПД)
- Серверы: РФ (ФЗ-152)
- Позиционирование: инструмент кризисной интервенции, **НЕ медицинское изделие**
- Запрещённые слова в продукте: «диагностика», «лечение», «терапия» (в медицинском смысле)

---

## 🤝 Контакты

Разработка ведётся одним разработчиком + Claude Code.

Подробности — в [CLAUDE.md](CLAUDE.md).
