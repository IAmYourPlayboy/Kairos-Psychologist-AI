# Слой восприятия Кайроса: план имплементации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Заменить rule-based детекторы кризиса и ветки терапии полноценным слоем восприятия, который понимает намёки, помнит контекст и подстраивается под пользователя.

**Architecture:** 4 связанных компонента: **Brain** (статичные знания, уже есть), **Dossier** (двухуровневые папки фактов с цитатами, на user_id), **Mood** (6 осей в Redis, обновляется правилами), **MessageAnalyzer** (отдельный LLM-вызов на каждое сообщение с богатым JSON-выходом). Фоновый **ReflectionAgent** через 15 минут после последнего сообщения через Celery извлекает факты и обновляет досье. Старый код (`crisis/detector.py`, `crisis/keywords.py`, `branch_selector.py`) удаляется в самом конце через strangler-pattern (флаг `use_perception_layer`, переключение, очистка).

**Tech Stack:**
- Backend: FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, httpx
- Очереди: Celery + Redis (broker + result backend)
- БД: SQLite (dev), PostgreSQL (prod)
- Хранилище состояния: Redis (Mood, scheduling)
- Тесты: pytest, pytest-asyncio, unittest.mock
- Frontend: Next.js 14 + TypeScript (только для Фазы 6 — UI досье)

**Спецификация:** [`docs/superpowers/specs/2026-05-02-perception-layer-design.md`](../specs/2026-05-02-perception-layer-design.md)

---

## Фазы и checkpoint-ы

| Фаза | Что в ней | Зависит от |
|---|---|---|
| 0 | Предусловия: Redis, Celery, settings-флаг, общая структура папок | — |
| 1 | Модели данных Dossier (3 новые таблицы) + миграция + smoke-тесты | 0 |
| 2 | MessageAnalyzer — отдельный LLM-вызов с PerceptionReport | 0 |
| 3 | Mood — 6 осей в Redis, формулы обновления, тесты | 0, 2 |
| 4 | PromptBuilder + новый чат-эндпоинт под флагом (старый параллельно) | 1, 2, 3 |
| 5 | ReflectionAgent — Celery task, полный цикл extract→classify→dedupe→update | 1, 4 |
| 6 | UI досье + переключение флага + удаление старого кода + PROGRESS.md | 5 |

**Между фазами — обязательный checkpoint**: ручная проверка пользователем, что фаза работает. Не двигаемся дальше пока пользователь не подтвердит.

---

## Фаза 0: Предусловия

**Цель:** добавить Redis и Celery в инфраструктуру, завести settings-флаг, чтобы дальше можно было строить.

### Задача 0.1: Установить Redis локально или подключить удалённый

**Файлы:**
- Modify: `backend/.env` (добавить REDIS_URL если нужно)
- Modify: `backend/.env.example`
- Modify: `backend/app/config.py` — поле уже есть, проверить дефолт

- [ ] **Шаг 1: Проверить, есть ли Redis на машине разработчика**

Запусти: `redis-cli ping`

Ожидаемый результат: `PONG`. Если Redis нет на Mac — `brew install redis && brew services start redis`. На Windows — Docker контейнер `docker run -d --name kairos-redis -p 6379:6379 redis:7-alpine`. Альтернатива: использовать удалённый Redis на VPS Timeweb Cloud (если он уже есть).

- [ ] **Шаг 2: Убедиться, что `REDIS_URL` корректный в `.env`**

Открой `backend/.env`, проверь строку:
```
REDIS_URL=redis://localhost:6379/0
```
(если используешь удалённый Redis — замени host).

- [ ] **Шаг 3: Добавить REDIS_URL в `.env.example` если ещё не там**

Открой `backend/.env.example`, убедись что есть:
```
REDIS_URL=redis://localhost:6379/0
```

- [ ] **Шаг 4: Проверка подключения из Python**

В корне `backend/` запусти:
```
python -c "import redis.asyncio as redis; import asyncio; asyncio.run(redis.from_url('redis://localhost:6379/0').ping())"
```

Если выдаёт `ImportError: No module named redis` — это OK, Redis-клиент мы поставим в следующей задаче.

- [ ] **Шаг 5: Коммит**

Если ничего не менял (`.env` уже был корректный) — коммита не нужно. Иначе:

```
git add backend/.env.example
git commit -m "chore(perception): document REDIS_URL in env example"
```

---

### Задача 0.2: Добавить зависимости Redis и Celery в pyproject.toml

**Файлы:**
- Modify: `backend/pyproject.toml`

- [ ] **Шаг 1: Открыть `backend/pyproject.toml`, найти секцию `dependencies`**

- [ ] **Шаг 2: Добавить новые зависимости в `dependencies`**

После строки `"pyyaml>=6.0",` добавь:
```toml
    # === Слой восприятия (Сессия 18+) ===
    "redis[hiredis]>=5.2.0",          # Async Redis-клиент для Mood и rate limit
    "celery>=5.4.0",                  # Фоновый брокер для ReflectionAgent
    "celery[redis]>=5.4.0",           # Поддержка Redis как broker/backend
```

- [ ] **Шаг 3: Установить новые зависимости**

В корне `backend/` выполни:
```
pip install -e ".[dev]"
```

Ожидаемый результат: `Successfully installed redis-5.x.x celery-5.4.x ...`.

- [ ] **Шаг 4: Проверить импорт**

```
python -c "import redis.asyncio; import celery; print('ok')"
```

Ожидаемый результат: `ok`.

- [ ] **Шаг 5: Коммит**

```
git add backend/pyproject.toml
git commit -m "feat(perception): add redis and celery dependencies"
```

---

### Задача 0.3: Завести settings-флаг `use_perception_layer`

**Файлы:**
- Modify: `backend/app/config.py`
- Modify: `backend/.env.example`

- [ ] **Шаг 1: Открыть `backend/app/config.py`, найти класс `Settings`**

- [ ] **Шаг 2: Добавить новые поля после `cors_origins`**

```python
    # === Слой восприятия (Фаза 0+) ===
    # Флаг включения нового слоя восприятия (Фаза 4 → переключение).
    # Пока false — работает старый rule-based pipeline.
    use_perception_layer: bool = False

    # Celery broker (тот же Redis, но другая БД для разделения)
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Через сколько секунд после последнего сообщения запускать ReflectionAgent
    reflection_delay_seconds: int = 15 * 60  # 15 минут
```

- [ ] **Шаг 3: Добавить дефолты в `backend/.env.example`**

В конце файла, перед последней пустой строкой, добавь блок:
```
# === Слой восприятия (Сессия 18+) ===
USE_PERCEPTION_LAYER=false
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
REFLECTION_DELAY_SECONDS=900
```

- [ ] **Шаг 4: Проверить загрузку**

```
python -c "from app.config import settings; print(settings.use_perception_layer, settings.celery_broker_url)"
```

Ожидаемый результат: `False redis://localhost:6379/1`.

- [ ] **Шаг 5: Коммит**

```
git add backend/app/config.py backend/.env.example
git commit -m "feat(perception): add use_perception_layer flag and celery config"
```

---

### Задача 0.4: Скелет директории `core/perception/`

**Файлы:**
- Create: `backend/app/core/perception/__init__.py`
- Create: `backend/app/core/perception/README.md`

- [ ] **Шаг 1: Создать `backend/app/core/perception/__init__.py`**

Содержимое:
```python
"""Слой восприятия Кайроса.

Группа компонентов, превращающих сообщение пользователя в богатый контекст
для основной LLM:

- analyzer.py     — MessageAnalyzer (LLM-вызов, PerceptionReport)
- mood.py         — Mood (6 осей в Redis, формулы обновления)
- dossier.py      — DossierService (CRUD над фактами/цитатами)
- folders.py      — Фиксированный список папок и подпапок
- prompt_builder.py — Сборка промпта для основной LLM
- types.py        — Pydantic-модели (PerceptionReport, MoodState и т.д.)

См. полный дизайн: docs/superpowers/specs/2026-05-02-perception-layer-design.md
"""
```

- [ ] **Шаг 2: Создать `backend/app/core/perception/README.md`**

Содержимое:
```markdown
# Слой восприятия

Реализация согласно [`specs/2026-05-02-perception-layer-design.md`](../../../../docs/superpowers/specs/2026-05-02-perception-layer-design.md).

Не трогать без чтения спецификации.
```

- [ ] **Шаг 3: Коммит**

```
git add backend/app/core/perception/
git commit -m "feat(perception): scaffold core/perception package"
```

---

### Checkpoint Фазы 0

Прежде чем идти в Фазу 1, проверь:

- [ ] `redis-cli ping` отвечает `PONG`.
- [ ] `python -c "import redis.asyncio; import celery"` проходит.
- [ ] `python -c "from app.config import settings; print(settings.use_perception_layer)"` печатает `False`.
- [ ] Папка `backend/app/core/perception/` существует с `__init__.py` и `README.md`.

Если всё ОК — переходим в Фазу 1.

---

## Фаза 1: Модели данных Dossier

**Цель:** добавить 3 новые таблицы (`dossier_facts`, `dossier_quotes`, `dossier_checkpoints`), сгенерировать Alembic-миграцию, написать smoke-тесты на CRUD.

### Задача 1.1: Список фиксированных папок и подпапок

**Файлы:**
- Create: `backend/app/core/perception/folders.py`
- Test: `backend/tests/perception/test_folders.py`

- [ ] **Шаг 1: Создать `backend/tests/perception/__init__.py`**

Пустой файл, чтобы pytest нашёл тесты.

- [ ] **Шаг 2: Написать тест `backend/tests/perception/test_folders.py`**

```python
"""Тесты структуры папок досье."""

from app.core.perception.folders import (
    TOP_LEVEL_FOLDERS,
    SUBFOLDERS,
    is_valid_folder,
    is_valid_subfolder,
)


def test_thirteen_top_folders_plus_custom():
    """Верхний уровень = 13 фиксированных + custom."""
    assert "identity" in TOP_LEVEL_FOLDERS
    assert "family" in TOP_LEVEL_FOLDERS
    assert "custom" in TOP_LEVEL_FOLDERS
    assert len(TOP_LEVEL_FOLDERS) == 14


def test_subfolders_for_family():
    """family имеет правильные подпапки."""
    assert SUBFOLDERS["family"] == {"parents", "siblings", "grandparents", "extended"}


def test_subfolders_for_health():
    assert "appearance" in SUBFOLDERS["health"]
    assert "mental" in SUBFOLDERS["health"]


def test_is_valid_folder():
    assert is_valid_folder("family") is True
    assert is_valid_folder("nonsense") is False
    # Custom-папки разрешены через "custom"
    assert is_valid_folder("custom") is True


def test_is_valid_subfolder_within_folder():
    assert is_valid_subfolder("family", "parents") is True
    assert is_valid_subfolder("family", "wrong") is False
    # Папки без обязательных подпапок (например identity) разрешают None
    assert is_valid_subfolder("identity", None) is True


def test_subfolder_required_for_family():
    """family требует подпапку (нет валидного None)."""
    assert is_valid_subfolder("family", None) is False


def test_custom_folder_accepts_any_subfolder():
    """custom — special case, любая подпапка валидна (это пользовательская папка)."""
    assert is_valid_subfolder("custom", "medical_visits") is True
    assert is_valid_subfolder("custom", None) is False  # custom БЕЗ имени бессмысленна
```

- [ ] **Шаг 3: Запустить тест — должен упасть с ImportError**

```
cd backend && pytest tests/perception/test_folders.py -v
```

Ожидаемый результат: `ImportError: No module named 'app.core.perception.folders'`.

- [ ] **Шаг 4: Реализовать `backend/app/core/perception/folders.py`**

```python
"""Фиксированный список папок и подпапок досье.

Дизайн: §4.1 в spec.

Правила:
- 13 фиксированных верхнеуровневых папок + специальная "custom" для
  пользовательских папок (создаваемых ReflectionAgent).
- Подпапки для большинства папок фиксированы. Если папка их требует —
  подпапка не может быть NULL.
- Папки и подпапки именуются на английском snake_case.
- "custom" папка — особый случай: подпапка играет роль имени
  пользовательской категории (например custom/medical_visits).
"""

from __future__ import annotations

# Фиксированные папки верхнего уровня
TOP_LEVEL_FOLDERS: frozenset[str] = frozenset({
    "identity",
    "childhood",
    "family",
    "relationships",
    "work_school",
    "losses",
    "triggers",
    "resources",
    "values",
    "health",
    "crisis_history",
    "goals",
    "routines",
    "custom",  # для пользовательских папок
})


# Допустимые подпапки. Пустой набор = подпапка опциональна (может быть None).
SUBFOLDERS: dict[str, frozenset[str]] = {
    "identity": frozenset(),  # подпапки не нужны
    "childhood": frozenset({"family", "school", "events"}),
    "family": frozenset({"parents", "siblings", "grandparents", "extended"}),
    "relationships": frozenset({"friends", "romantic", "school_peers", "colleagues"}),
    "work_school": frozenset({"current", "past", "performance"}),
    "losses": frozenset({"death", "breakup", "relocation", "other"}),
    "triggers": frozenset({"sensory", "situational", "relational"}),
    "resources": frozenset({"people", "activities", "skills", "places"}),
    "values": frozenset(),
    "health": frozenset({"body", "sleep", "illness", "appearance", "mental"}),
    "crisis_history": frozenset({"past_attempts", "past_episodes", "protective_factors"}),
    "goals": frozenset({"short_term", "long_term"}),
    "routines": frozenset({"daily", "weekly", "rituals"}),
    "custom": frozenset(),  # любое имя разрешено
}

# Папки, для которых подпапка ОБЯЗАТЕЛЬНА (без неё факт не записать).
REQUIRES_SUBFOLDER: frozenset[str] = frozenset({
    "family",
    "relationships",
    "triggers",
    "health",
    "custom",  # custom всегда требует имя пользовательской папки
})


def is_valid_folder(folder: str) -> bool:
    """Проверить, что folder из списка верхнего уровня."""
    return folder in TOP_LEVEL_FOLDERS


def is_valid_subfolder(folder: str, subfolder: str | None) -> bool:
    """Проверить, что (folder, subfolder) — допустимая пара.

    Логика:
    - "custom" — подпапка обязательна, но любая (это имя пользовательской папки).
    - Если folder требует подпапку (REQUIRES_SUBFOLDER) — она должна быть
      из SUBFOLDERS[folder].
    - Если folder подпапку не требует — допустимо None или одна из SUBFOLDERS[folder].
    """
    if not is_valid_folder(folder):
        return False

    if folder == "custom":
        # custom требует non-empty имя, но любое (snake_case)
        return subfolder is not None and len(subfolder) > 0

    if folder in REQUIRES_SUBFOLDER:
        if subfolder is None:
            return False
        return subfolder in SUBFOLDERS[folder]

    # Подпапка опциональна
    if subfolder is None:
        return True
    return subfolder in SUBFOLDERS[folder]
```

- [ ] **Шаг 5: Запустить тест — должен пройти**

```
cd backend && pytest tests/perception/test_folders.py -v
```

Ожидаемый результат: `7 passed`.

- [ ] **Шаг 6: Коммит**

```
git add backend/app/core/perception/folders.py backend/tests/perception/
git commit -m "feat(perception): define dossier folder taxonomy with validation"
```

---

### Задача 1.2: SQLAlchemy-модели Dossier

**Файлы:**
- Create: `backend/app/data/dossier_models.py`
- Modify: `backend/app/data/__init__.py` (экспорт)

- [ ] **Шаг 1: Создать `backend/app/data/dossier_models.py`**

```python
"""SQLAlchemy модели для досье пользователя.

Дизайн: §4 в spec.

3 таблицы:
- dossier_facts        — факт о пользователе (один уровень — один факт)
- dossier_quotes       — буквальные цитаты пользователя, связанные с фактом
- dossier_checkpoints  — где ReflectionAgent остановился для каждого user_id

Все ID — String(36) UUID для совместимости SQLite ↔ PostgreSQL.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.models import Base, _utcnow, _new_uuid


# ============================================================================
# Факты досье
# ============================================================================


class DossierFact(Base):
    """Один факт о пользователе.

    Хранится в папке/подпапке (см. core/perception/folders.py).
    Содержит summary (формулировку), tags (английский kebab-case),
    severity и confidence.

    Связан с цитатами (один-ко-многим) и опционально с superseded_by
    (если факт устарел и заменён новым).
    """

    __tablename__ = "dossier_facts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # Папка и подпапка (см. folders.py для допустимых значений)
    folder: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    subfolder: Mapped[str | None] = mapped_column(String(50), nullable=True)

    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Список тэгов хранится как JSON (SQLite-совместимо).
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    severity: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    first_mentioned: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )
    last_mentioned: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )
    times_mentioned: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # ID сессий и сообщений, из которых факт извлечён (хранятся как JSON-массивы)
    source_session_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    source_message_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # Если факт устарел и заменён — ссылка на новый. Старые НЕ удаляем.
    superseded_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("dossier_facts.id"), nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )

    # Связи
    quotes: Mapped[list[DossierQuote]] = relationship(
        "DossierQuote", back_populates="fact",
        cascade="all, delete-orphan",
        order_by="DossierQuote.created_at",
    )

    def __repr__(self) -> str:
        loc = self.folder if not self.subfolder else f"{self.folder}/{self.subfolder}"
        return (
            f"<DossierFact id={self.id[:8]} {loc} "
            f"sev={self.severity:.2f} '{self.summary[:30]}...'>"
        )


# ============================================================================
# Цитаты пользователя (доказательная база факта)
# ============================================================================


class DossierQuote(Base):
    """Буквальная цитата пользователя, на основании которой факт извлечён.

    Один факт может иметь несколько цитат (повторные упоминания → новые цитаты).
    """

    __tablename__ = "dossier_quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    fact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("dossier_facts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id"), nullable=False,
    )
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("messages.id"), nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )

    # Связи
    fact: Mapped[DossierFact] = relationship(
        "DossierFact", back_populates="quotes",
    )

    def __repr__(self) -> str:
        return f"<DossierQuote fact={self.fact_id[:8]} '{self.text[:40]}...'>"


# ============================================================================
# Чекпойнт ReflectionAgent (один на пользователя)
# ============================================================================


class DossierCheckpoint(Base):
    """Закладка ReflectionAgent: где остановилась обработка.

    Один чекпойнт на user_id. При каждом успешном проходе агента
    last_processed_message_id сдвигается на самое последнее обработанное
    сообщение.
    """

    __tablename__ = "dossier_checkpoints"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # NULL до первого прохода агента
    last_processed_message_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("messages.id"), nullable=True,
    )
    last_processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    facts_extracted_total: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<DossierCheckpoint user={self.user_id[:8]} "
            f"facts={self.facts_extracted_total}>"
        )
```

- [ ] **Шаг 2: Обновить `backend/app/data/__init__.py` для экспорта**

Открой `backend/app/data/__init__.py`, найди существующий блок импортов моделей, добавь после:

```python
from app.data.dossier_models import (
    DossierFact,
    DossierQuote,
    DossierCheckpoint,
)
```

И добавь их в `__all__` если он там есть.

- [ ] **Шаг 3: Проверить импорт**

```
cd backend && python -c "from app.data import DossierFact, DossierQuote, DossierCheckpoint; print('ok')"
```

Ожидаемый результат: `ok`.

- [ ] **Шаг 4: Коммит**

```
git add backend/app/data/dossier_models.py backend/app/data/__init__.py
git commit -m "feat(perception): add Dossier SQLAlchemy models (facts, quotes, checkpoint)"
```

---

### Задача 1.3: Alembic-миграция для новых таблиц

**Файлы:**
- Create: `backend/alembic/versions/<auto>_add_dossier_tables.py`

- [ ] **Шаг 1: Сгенерировать миграцию автоматически**

В корне `backend/`:
```
alembic revision --autogenerate -m "add dossier tables"
```

Ожидаемый результат: создан файл `backend/alembic/versions/<timestamp>_add_dossier_tables.py`. В нём — три `op.create_table()` для `dossier_facts`, `dossier_quotes`, `dossier_checkpoints`.

- [ ] **Шаг 2: Открыть сгенерированный файл и проверить**

Должно быть:
- `op.create_table('dossier_facts', ...)` с полями id, user_id, folder, subfolder, summary, tags (JSON), severity, confidence, first_mentioned, last_mentioned, times_mentioned, source_session_ids (JSON), source_message_ids (JSON), superseded_by, created_at.
- `op.create_table('dossier_quotes', ...)` с полями id, fact_id, text, session_id, message_id, created_at.
- `op.create_table('dossier_checkpoints', ...)` с полями user_id (PK), last_processed_message_id, last_processed_at, facts_extracted_total, created_at, updated_at.
- В downgrade — `op.drop_table()` в обратном порядке.

Если автогенератор пропустил индексы — добавь руками:
```python
    op.create_index(op.f('ix_dossier_facts_user_id'), 'dossier_facts', ['user_id'])
    op.create_index(op.f('ix_dossier_facts_folder'), 'dossier_facts', ['folder'])
    op.create_index(op.f('ix_dossier_quotes_fact_id'), 'dossier_quotes', ['fact_id'])
```

- [ ] **Шаг 3: Применить миграцию**

```
alembic upgrade head
```

Ожидаемый результат: `Running upgrade <prev> -> <new>, add dossier tables`.

- [ ] **Шаг 4: Проверить что таблицы созданы**

```
python -c "from app.data.database import engine; from sqlalchemy import inspect; import asyncio; \
async def f(): \
  async with engine.begin() as conn: \
    res = await conn.run_sync(lambda c: inspect(c).get_table_names()); \
    print(res); \
asyncio.run(f())"
```

Ожидаемый результат: список таблиц включает `dossier_facts`, `dossier_quotes`, `dossier_checkpoints`.

- [ ] **Шаг 5: Коммит**

```
git add backend/alembic/versions/
git commit -m "feat(perception): alembic migration for dossier tables"
```

---

### Задача 1.4: DossierService — высокоуровневый CRUD

**Файлы:**
- Create: `backend/app/core/perception/dossier.py`
- Test: `backend/tests/perception/test_dossier.py`

- [ ] **Шаг 1: Написать тест `backend/tests/perception/test_dossier.py`**

```python
"""Тесты DossierService — высокоуровневый CRUD над фактами/цитатами."""

from __future__ import annotations

import os
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4

# Используем отдельный файл SQLite для тестов
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_dossier.db"
os.environ["LLM_API_KEY"] = "test-key"

from app.core.perception.dossier import DossierService
from app.data.database import create_all_tables, drop_all_tables, async_session_factory
from app.data.models import User, ChatSession, Message


@pytest_asyncio.fixture
async def db_with_user():
    """Создаёт чистую БД с одним пользователем и одной сессией с одним сообщением."""
    await drop_all_tables()
    await create_all_tables()

    async with async_session_factory() as db:
        user = User(id=str(uuid4()), email="test@example.com")
        db.add(user)
        session = ChatSession(id=str(uuid4()), user_id=user.id)
        db.add(session)
        msg = Message(id=str(uuid4()), session_id=session.id, role="user", content="мама ругает за макияж")
        db.add(msg)
        await db.commit()
        yield {"user_id": user.id, "session_id": session.id, "message_id": msg.id}

    await drop_all_tables()


async def test_create_fact(db_with_user):
    """add_fact() создаёт факт с цитатой."""
    async with async_session_factory() as db:
        service = DossierService(db)
        fact = await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="family",
            subfolder="parents",
            summary="Мама критикует внешность",
            tags=["mom-criticism", "appearance-pressure"],
            severity=0.6,
            confidence=0.8,
            quotes=[{
                "text": "мама ругает за макияж",
                "session_id": db_with_user["session_id"],
                "message_id": db_with_user["message_id"],
            }],
        )

    assert fact.id
    assert fact.folder == "family"
    assert fact.subfolder == "parents"
    assert fact.times_mentioned == 1
    assert len(fact.tags) == 2


async def test_get_facts_by_folder(db_with_user):
    """get_facts() возвращает факты в нужной папке."""
    async with async_session_factory() as db:
        service = DossierService(db)
        await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="family",
            subfolder="parents",
            summary="Мама критикует",
            tags=["mom"],
            severity=0.6,
            confidence=0.8,
            quotes=[],
        )
        await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="health",
            subfolder="appearance",
            summary="Не нравится своё отражение",
            tags=["body-image"],
            severity=0.4,
            confidence=0.7,
            quotes=[],
        )

    async with async_session_factory() as db:
        service = DossierService(db)
        family = await service.get_facts_by_folders(
            db_with_user["user_id"], folders=["family"],
        )
        assert len(family) == 1
        assert family[0].summary == "Мама критикует"


async def test_top_relevant_facts(db_with_user):
    """top_relevant_facts() сортирует по severity * recency."""
    async with async_session_factory() as db:
        service = DossierService(db)
        # Высокая severity, упомянуто давно
        await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="crisis_history", subfolder="past_episodes",
            summary="Кризис 2023",
            tags=[], severity=0.95, confidence=0.9, quotes=[],
        )
        # Низкая severity, упомянуто недавно
        await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="goals", subfolder="short_term",
            summary="Сдать экзамен",
            tags=[], severity=0.2, confidence=0.6, quotes=[],
        )

    async with async_session_factory() as db:
        service = DossierService(db)
        top = await service.top_relevant_facts(db_with_user["user_id"], limit=5)
        # Кризис должен быть первым (severity бьёт recency)
        assert top[0].summary == "Кризис 2023"


async def test_update_fact_adds_quote(db_with_user):
    """update_fact_with_new_quote() добавляет цитату и счётчик."""
    async with async_session_factory() as db:
        service = DossierService(db)
        fact = await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="family", subfolder="parents",
            summary="Мама критикует",
            tags=["mom"], severity=0.6, confidence=0.8,
            quotes=[{
                "text": "мама ругает",
                "session_id": db_with_user["session_id"],
                "message_id": db_with_user["message_id"],
            }],
        )
        fact_id = fact.id

    async with async_session_factory() as db:
        service = DossierService(db)
        updated = await service.update_fact_with_new_quote(
            fact_id=fact_id,
            new_quote={
                "text": "мама опять про мою помаду",
                "session_id": db_with_user["session_id"],
                "message_id": db_with_user["message_id"],
            },
        )

    assert updated.times_mentioned == 2
    assert len(updated.quotes) == 2
```

- [ ] **Шаг 2: Запустить тесты — должны упасть с ImportError**

```
cd backend && pytest tests/perception/test_dossier.py -v
```

Ожидаемый результат: `ImportError: No module named 'app.core.perception.dossier'`.

- [ ] **Шаг 3: Реализовать `backend/app/core/perception/dossier.py`**

```python
"""Высокоуровневый CRUD над фактами и цитатами досье.

Этот модуль НЕ работает с LLM — он работает только с БД.
LLM-ориентированные операции (extract, classify, dedupe) живут в
ReflectionAgent (Фаза 5).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.perception.folders import is_valid_subfolder
from app.data.dossier_models import (
    DossierFact,
    DossierQuote,
    DossierCheckpoint,
)


class QuoteInput(TypedDict):
    """Структура цитаты при создании факта."""
    text: str
    session_id: str
    message_id: str


class DossierService:
    """Сервис над таблицами досье. Принимает AsyncSession в конструктор."""

    def __init__(self, db: AsyncSession):
        self._db = db

    # ------------------------------------------------------------------
    # Создание / обновление
    # ------------------------------------------------------------------

    async def add_fact(
        self,
        *,
        user_id: str,
        folder: str,
        subfolder: str | None,
        summary: str,
        tags: list[str],
        severity: float,
        confidence: float,
        quotes: list[QuoteInput],
    ) -> DossierFact:
        """Создать новый факт. Валидирует folder/subfolder.

        Raises:
            ValueError: если папка/подпапка не валидны.
        """
        if not is_valid_subfolder(folder, subfolder):
            raise ValueError(f"Invalid folder/subfolder: {folder}/{subfolder}")

        now = datetime.now(timezone.utc)
        fact = DossierFact(
            id=str(uuid4()),
            user_id=user_id,
            folder=folder,
            subfolder=subfolder,
            summary=summary,
            tags=tags,
            severity=severity,
            confidence=confidence,
            first_mentioned=now,
            last_mentioned=now,
            times_mentioned=max(1, len(quotes)),
            source_session_ids=list({q["session_id"] for q in quotes}),
            source_message_ids=[q["message_id"] for q in quotes],
        )
        self._db.add(fact)
        await self._db.flush()  # получить fact.id перед созданием quotes

        for q in quotes:
            quote = DossierQuote(
                id=str(uuid4()),
                fact_id=fact.id,
                text=q["text"],
                session_id=q["session_id"],
                message_id=q["message_id"],
            )
            self._db.add(quote)

        await self._db.commit()
        await self._db.refresh(fact, attribute_names=["quotes"])
        return fact

    async def update_fact_with_new_quote(
        self,
        *,
        fact_id: str,
        new_quote: QuoteInput,
        new_severity: float | None = None,
    ) -> DossierFact:
        """Добавить цитату к существующему факту, увеличить счётчик упоминаний."""
        fact = await self._db.get(DossierFact, fact_id)
        if fact is None:
            raise ValueError(f"Fact not found: {fact_id}")

        quote = DossierQuote(
            id=str(uuid4()),
            fact_id=fact.id,
            text=new_quote["text"],
            session_id=new_quote["session_id"],
            message_id=new_quote["message_id"],
        )
        self._db.add(quote)

        fact.times_mentioned += 1
        fact.last_mentioned = datetime.now(timezone.utc)
        if new_severity is not None:
            fact.severity = max(fact.severity, new_severity)

        # Дополним массивы источников
        if new_quote["session_id"] not in fact.source_session_ids:
            fact.source_session_ids = [*fact.source_session_ids, new_quote["session_id"]]
        fact.source_message_ids = [*fact.source_message_ids, new_quote["message_id"]]

        await self._db.commit()
        await self._db.refresh(fact, attribute_names=["quotes"])
        return fact

    async def supersede_fact(
        self,
        *,
        old_fact_id: str,
        new_fact_id: str,
    ) -> None:
        """Пометить старый факт как заменённый новым (НЕ удалять)."""
        fact = await self._db.get(DossierFact, old_fact_id)
        if fact is None:
            raise ValueError(f"Fact not found: {old_fact_id}")
        fact.superseded_by = new_fact_id
        await self._db.commit()

    # ------------------------------------------------------------------
    # Чтение
    # ------------------------------------------------------------------

    async def get_facts_by_folders(
        self,
        user_id: str,
        *,
        folders: list[str] | None = None,
        include_superseded: bool = False,
    ) -> list[DossierFact]:
        """Получить факты пользователя, опционально отфильтрованные по папкам."""
        stmt = (
            select(DossierFact)
            .where(DossierFact.user_id == user_id)
            .options(selectinload(DossierFact.quotes))
        )
        if folders:
            stmt = stmt.where(DossierFact.folder.in_(folders))
        if not include_superseded:
            stmt = stmt.where(DossierFact.superseded_by.is_(None))

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def top_relevant_facts(
        self,
        user_id: str,
        *,
        limit: int = 5,
    ) -> list[DossierFact]:
        """Топ-N самых релевантных фактов.

        Эвристика: severity * recency_factor.
        recency_factor = exp(-days_since_last_mention / 30).

        В Python — потому что вычисление complex и SQLite-универсальное.
        """
        from math import exp

        all_facts = await self.get_facts_by_folders(user_id)
        now = datetime.now(timezone.utc)

        def score(f: DossierFact) -> float:
            days = max(0, (now - f.last_mentioned).total_seconds() / 86400)
            recency = exp(-days / 30)
            return f.severity * recency * f.confidence

        all_facts.sort(key=score, reverse=True)
        return all_facts[:limit]

    async def all_user_facts(self, user_id: str) -> list[DossierFact]:
        """ВСЕ факты пользователя (для UI просмотра в Фазе 6)."""
        return await self.get_facts_by_folders(user_id, include_superseded=True)

    # ------------------------------------------------------------------
    # Удаление (для UI «удалить факт» / «удалить всё досье», Фаза 6)
    # ------------------------------------------------------------------

    async def delete_fact(self, *, user_id: str, fact_id: str) -> None:
        """Удалить факт пользователя. Цитаты уберутся каскадом."""
        fact = await self._db.get(DossierFact, fact_id)
        if fact is None or fact.user_id != user_id:
            raise ValueError("Fact not found or doesn't belong to user")
        await self._db.delete(fact)
        await self._db.commit()

    async def delete_all_for_user(self, user_id: str) -> int:
        """Удалить ВСЁ досье пользователя. Возвращает количество удалённых фактов."""
        facts = await self.get_facts_by_folders(user_id, include_superseded=True)
        count = len(facts)
        for f in facts:
            await self._db.delete(f)
        # Также сбрасываем чекпойнт
        cp = await self._db.get(DossierCheckpoint, user_id)
        if cp:
            await self._db.delete(cp)
        await self._db.commit()
        return count

    # ------------------------------------------------------------------
    # Чекпойнт
    # ------------------------------------------------------------------

    async def get_checkpoint(self, user_id: str) -> DossierCheckpoint | None:
        return await self._db.get(DossierCheckpoint, user_id)

    async def update_checkpoint(
        self,
        *,
        user_id: str,
        last_processed_message_id: str,
        facts_extracted: int,
    ) -> DossierCheckpoint:
        cp = await self._db.get(DossierCheckpoint, user_id)
        now = datetime.now(timezone.utc)
        if cp is None:
            cp = DossierCheckpoint(
                user_id=user_id,
                last_processed_message_id=last_processed_message_id,
                last_processed_at=now,
                facts_extracted_total=facts_extracted,
                created_at=now,
                updated_at=now,
            )
            self._db.add(cp)
        else:
            cp.last_processed_message_id = last_processed_message_id
            cp.last_processed_at = now
            cp.facts_extracted_total += facts_extracted
            cp.updated_at = now
        await self._db.commit()
        await self._db.refresh(cp)
        return cp
```

- [ ] **Шаг 4: Запустить тесты — должны пройти**

```
cd backend && pytest tests/perception/test_dossier.py -v
```

Ожидаемый результат: `4 passed`.

- [ ] **Шаг 5: Коммит**

```
git add backend/app/core/perception/dossier.py backend/tests/perception/test_dossier.py
git commit -m "feat(perception): add DossierService with CRUD over facts/quotes"
```

---

### Checkpoint Фазы 1

Перед переходом в Фазу 2 проверь:

- [ ] `alembic upgrade head` прошёл без ошибок.
- [ ] В БД есть таблицы `dossier_facts`, `dossier_quotes`, `dossier_checkpoints`.
- [ ] `pytest tests/perception/ -v` — все тесты зелёные.
- [ ] В git нет staged-изменений (всё закоммичено).

---

## Фаза 2: MessageAnalyzer

**Цель:** реализовать отдельный LLM-вызов, который читает сообщение пользователя + контекст и возвращает структурированный `PerceptionReport`. Тестируется на mock LLM-провайдере.

### Задача 2.1: Pydantic-типы PerceptionReport

**Файлы:**
- Create: `backend/app/core/perception/types.py`
- Test: `backend/tests/perception/test_types.py`

- [ ] **Шаг 1: Написать тесты `backend/tests/perception/test_types.py`**

```python
"""Тесты Pydantic-типов слоя восприятия."""

import pytest
from pydantic import ValidationError

from app.core.perception.types import PerceptionReport, MoodState


def test_perception_report_minimal():
    """Минимальный валидный PerceptionReport."""
    r = PerceptionReport(
        risk_level="normal",
        dominant_emotion="нейтрально",
        secondary_emotions=[],
        theme="general",
        hidden_signals=[],
        open_questions=[],
        what_user_needs="ждёт ответа",
        trust_level=0.7,
        folder_hints=[],
        inner_monologue="всё спокойно",
    )
    assert r.risk_level == "normal"


def test_perception_report_immediate_risk():
    r = PerceptionReport(
        risk_level="immediate",
        dominant_emotion="отчаяние",
        secondary_emotions=["безысходность"],
        theme="suicide",
        hidden_signals=["намёк на план"],
        open_questions=["спросить о безопасности"],
        what_user_needs="безопасный план + контакты",
        trust_level=0.9,
        folder_hints=["crisis_history/past_attempts"],
        inner_monologue="это серьёзно. не пропустить.",
    )
    assert r.risk_level == "immediate"
    assert "безысходность" in r.secondary_emotions


def test_invalid_risk_level_rejected():
    with pytest.raises(ValidationError):
        PerceptionReport(
            risk_level="bad",  # noqa: лишь для теста
            dominant_emotion="x", secondary_emotions=[],
            theme="x", hidden_signals=[], open_questions=[],
            what_user_needs="x", trust_level=0.5,
            folder_hints=[], inner_monologue="x",
        )


def test_trust_level_clamped():
    """trust_level должен быть в [0.0, 1.0]."""
    with pytest.raises(ValidationError):
        PerceptionReport(
            risk_level="normal", dominant_emotion="x", secondary_emotions=[],
            theme="x", hidden_signals=[], open_questions=[],
            what_user_needs="x", trust_level=1.5,
            folder_hints=[], inner_monologue="x",
        )


def test_mood_state_defaults():
    m = MoodState.default()
    assert 0.0 <= m.alertness <= 1.0
    assert 0.0 <= m.warmth <= 1.0
    assert m.warmth > 0.5  # дефолт — теплее среднего


def test_mood_state_to_prompt_block():
    m = MoodState(
        alertness=0.85, warmth=0.95, pace=0.2,
        assertiveness=0.3, trust_in_user=0.9, depth=0.7,
    )
    block = m.to_prompt_block()
    assert "alertness: 0.85" in block
    assert "высокая" in block.lower() or "максим" in block.lower()
```

- [ ] **Шаг 2: Запустить тесты — упадут с ImportError**

```
cd backend && pytest tests/perception/test_types.py -v
```

- [ ] **Шаг 3: Реализовать `backend/app/core/perception/types.py`**

```python
"""Pydantic-модели слоя восприятия.

Эти типы — контракт между MessageAnalyzer, Mood и PromptBuilder.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ============================================================================
# PerceptionReport — выход MessageAnalyzer
# ============================================================================


RiskLevel = Literal["normal", "elevated", "high", "immediate"]


class PerceptionReport(BaseModel):
    """Структурированный отчёт анализатора об одном сообщении пользователя.

    Дизайн: §5.3 в spec.

    Используется:
    - В Mood.update() для расчёта новых значений 6 осей.
    - В PromptBuilder для сборки промпта основной LLM
      (folder_hints, inner_monologue, what_user_needs).
    - В data flywheel: логируется в messages.perception_json
      для будущего LoRA fine-tuning.
    """

    risk_level: RiskLevel = Field(
        ...,
        description="Кризисный уровень по восприятию анализатора",
    )

    dominant_emotion: str = Field(
        ..., min_length=1, max_length=50,
        description="Главная эмоция (русское слово)",
    )
    secondary_emotions: list[str] = Field(
        default_factory=list, max_length=5,
        description="До 5 второстепенных эмоций",
    )

    theme: str = Field(
        ..., min_length=1, max_length=100,
        description="Тема сообщения, slash-формат: 'family/dad-violence'",
    )

    hidden_signals: list[str] = Field(
        default_factory=list, max_length=5,
        description="Что недосказано / на что намекает пользователь",
    )

    open_questions: list[str] = Field(
        default_factory=list, max_length=5,
        description="О чём бы стоило спросить",
    )

    what_user_needs: str = Field(
        ..., min_length=1, max_length=300,
        description="Что нужно пользователю прямо сейчас (выслушать / совет / план / тишина)",
    )

    trust_level: float = Field(
        ..., ge=0.0, le=1.0,
        description="Насколько пользователь сейчас открыт (0=замкнут, 1=полная откровенность)",
    )

    folder_hints: list[str] = Field(
        default_factory=list, max_length=10,
        description="Какие папки досье подтянуть для контекста (формат: 'family/parents')",
    )

    inner_monologue: str = Field(
        ..., min_length=1, max_length=1000,
        description="Внутренние мысли Кайроса от первого лица. Только для админки/отладки. НЕ показывать пользователю.",
    )


# ============================================================================
# MoodState — внутреннее состояние Кайроса в разговоре
# ============================================================================


def _label(value: float) -> str:
    """Текстовая метка для значения 0.0-1.0."""
    if value >= 0.85:
        return "максимальная"
    if value >= 0.65:
        return "высокая"
    if value >= 0.4:
        return "средняя"
    if value >= 0.2:
        return "низкая"
    return "минимальная"


class MoodState(BaseModel):
    """6 осей внутреннего состояния Кайроса.

    Дизайн: §6 в spec.

    Все оси — 0.0-1.0. Хранится в Redis с ключом mood:{session_id}, TTL 24h.
    Сериализация — JSON.
    """

    alertness: float = Field(0.3, ge=0.0, le=1.0)
    warmth: float = Field(0.7, ge=0.0, le=1.0)
    pace: float = Field(0.5, ge=0.0, le=1.0)
    assertiveness: float = Field(0.4, ge=0.0, le=1.0)
    trust_in_user: float = Field(0.7, ge=0.0, le=1.0)
    depth: float = Field(0.4, ge=0.0, le=1.0)

    @classmethod
    def default(cls) -> "MoodState":
        """Дефолтное состояние при первом сообщении в новой сессии."""
        return cls()

    def to_prompt_block(self) -> str:
        """Сериализовать в текстовый блок для system prompt основной LLM.

        Формат человекочитаемый: число + текстовая метка + подсказка как вести.
        """
        return (
            "## ТЕКУЩЕЕ НАСТРОЕНИЕ (как тебе сейчас вести разговор)\n"
            f"- alertness: {self.alertness:.2f} ({_label(self.alertness)}) — "
            f"{'не пропускай сигналов риска' if self.alertness > 0.6 else 'риск умеренный'}\n"
            f"- warmth: {self.warmth:.2f} ({_label(self.warmth)}) — "
            f"{'давай больше тепла' if self.warmth > 0.7 else 'нейтральный тёплый тон'}\n"
            f"- pace: {self.pace:.2f} ({_label(self.pace)}) — "
            f"{'медленно, не торопи' if self.pace < 0.4 else 'нормальный темп'}\n"
            f"- assertiveness: {self.assertiveness:.2f} ({_label(self.assertiveness)}) — "
            f"{'не настаивай, следуй за пользователем' if self.assertiveness < 0.4 else 'можно вести'}\n"
            f"- trust_in_user: {self.trust_in_user:.2f} ({_label(self.trust_in_user)}) — "
            f"{'верь рассказу' if self.trust_in_user > 0.7 else 'уточняй детали'}\n"
            f"- depth: {self.depth:.2f} ({_label(self.depth)}) — "
            f"{'готова идти глубже' if self.depth > 0.5 else 'оставайся на поверхности'}"
        )
```

- [ ] **Шаг 4: Запустить тесты — должны пройти**

```
cd backend && pytest tests/perception/test_types.py -v
```

Ожидаемый результат: `5 passed`.

- [ ] **Шаг 5: Коммит**

```
git add backend/app/core/perception/types.py backend/tests/perception/test_types.py
git commit -m "feat(perception): add PerceptionReport and MoodState pydantic types"
```

---

### Задача 2.2: Промпт MessageAnalyzer

**Файлы:**
- Create: `backend/app/core/perception/analyzer_prompt.py`

- [ ] **Шаг 1: Создать `backend/app/core/perception/analyzer_prompt.py`**

```python
"""Системный промпт для MessageAnalyzer.

Это НЕ промпт основной LLM Кайроса — это отдельный «аналитический» промпт,
который превращает сообщение в JSON-отчёт.

Дизайн: §5 в spec.

Промпт умышленно требует от анализатора рассуждать (не классифицировать
по словарю), и явно говорит, что rule-based grep ушёл.
"""

ANALYZER_SYSTEM_PROMPT = """\
Ты — внутренний аналитик Кайроса. Ты НЕ отвечаешь пользователю.
Твоя задача — прочитать одно входящее сообщение пользователя в контексте \
последних реплик диалога и фактов из его досье, и вернуть структурированный JSON.

Этот JSON используется:
- для оценки уровня кризисного риска,
- для подбора того, какие факты досье подтянуть в основной ответ,
- для понимания, что пользователь сейчас НА САМОМ ДЕЛЕ хочет.

Ты ОБЯЗАН:
1. Читать намёки и недосказанное. «Они мне сказали кое-что» — это НЕ normal,
   это hidden signal с темой школы / отношений / угрозы — нужно уточнить.
2. Помнить контекст. Если пользователь раньше говорил о домашнем насилии,
   и сейчас пишет «папа опять...» — risk_level не normal.
3. Подбирать folder_hints из фиксированного списка папок:
   identity, childhood, family/(parents,siblings,grandparents,extended),
   relationships/(friends,romantic,school_peers,colleagues),
   work_school/(current,past,performance), losses/(death,breakup,relocation,other),
   triggers/(sensory,situational,relational), resources/(people,activities,skills,places),
   values, health/(body,sleep,illness,appearance,mental),
   crisis_history/(past_attempts,past_episodes,protective_factors),
   goals/(short_term,long_term), routines/(daily,weekly,rituals).
4. ВСЕГДА писать inner_monologue — это твои внутренние мысли «как Кайроса»
   о пользователе. От первого лица. 1-3 предложения.
5. ОТВЕЧАТЬ СТРОГО ВАЛИДНЫМ JSON по схеме (поля и типы):

{
  "risk_level": "normal" | "elevated" | "high" | "immediate",
  "dominant_emotion": str,
  "secondary_emotions": [str, ...] (до 5),
  "theme": str (slash-формат, например "family/dad-violence"),
  "hidden_signals": [str, ...] (до 5),
  "open_questions": [str, ...] (до 5),
  "what_user_needs": str (что нужно сейчас: выслушать/совет/план/тишина),
  "trust_level": float (0.0-1.0),
  "folder_hints": [str, ...] (формат "folder/subfolder", из списка выше, до 10),
  "inner_monologue": str (мысли Кайроса от 1 лица, 1-3 предложения)
}

Никакого текста вне JSON. Никаких объяснений. Никаких markdown-обёрток.
Только сырой JSON.
"""


def build_analyzer_user_prompt(
    *,
    current_message: str,
    history: list[dict[str, str]],
    dossier_summary: str,
) -> str:
    """Собрать user-часть запроса для анализатора.

    Args:
        current_message: текст текущего сообщения пользователя.
        history: последние реплики диалога [{"role": "user|assistant", "content": "..."}].
        dossier_summary: текстовая выжимка релевантных фактов
                         (или "пусто" если досье ещё не наполнено).

    Returns:
        Текст user message для LLM.
    """
    # Формат истории — компактный диалог без JSON-обёрток.
    history_lines = []
    for msg in history[-10:]:  # последние 10 реплик
        role = "Юзер" if msg["role"] == "user" else "Кайрос"
        history_lines.append(f"{role}: {msg['content']}")
    history_block = "\n".join(history_lines) if history_lines else "(история пуста)"

    return (
        f"## ДОСЬЕ ПОЛЬЗОВАТЕЛЯ (выжимка топ-фактов):\n"
        f"{dossier_summary}\n\n"
        f"## ИСТОРИЯ ДИАЛОГА (последние реплики):\n"
        f"{history_block}\n\n"
        f"## ТЕКУЩЕЕ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ:\n"
        f"{current_message}\n\n"
        f"Верни JSON по схеме."
    )
```

- [ ] **Шаг 2: Коммит**

```
git add backend/app/core/perception/analyzer_prompt.py
git commit -m "feat(perception): analyzer system prompt and user prompt builder"
```

---

### Задача 2.3: MessageAnalyzer — основной класс

**Файлы:**
- Create: `backend/app/core/perception/analyzer.py`
- Test: `backend/tests/perception/test_analyzer.py`

- [ ] **Шаг 1: Написать тест `backend/tests/perception/test_analyzer.py`**

```python
"""Тесты MessageAnalyzer.

LLM замокан — мы тестируем парсинг JSON, валидацию, обработку ошибок.
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, patch

from app.core.llm.base import LLMResponse, UsageStats
from app.core.perception.analyzer import MessageAnalyzer, AnalyzerError
from app.core.perception.types import PerceptionReport


def _llm_response(text: str) -> LLMResponse:
    return LLMResponse(
        text=text,
        usage=UsageStats(prompt_tokens=100, completion_tokens=50, total_tokens=150),
        response_time_ms=42.0,
    )


@pytest.fixture
def valid_json_text():
    return json.dumps({
        "risk_level": "elevated",
        "dominant_emotion": "страх",
        "secondary_emotions": ["беспомощность"],
        "theme": "school_peers/bullying",
        "hidden_signals": ["возможно угроза не озвучена"],
        "open_questions": ["что именно сказали?"],
        "what_user_needs": "хочет, чтобы её услышали",
        "trust_level": 0.85,
        "folder_hints": ["relationships/school_peers"],
        "inner_monologue": "она вернулась к этой теме сама. не торопить.",
    }, ensure_ascii=False)


async def test_analyze_parses_valid_json(valid_json_text):
    """analyze() корректно парсит JSON-ответ LLM."""
    analyzer = MessageAnalyzer()
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm_response(valid_json_text)),
    ):
        report = await analyzer.analyze(
            current_message="опять туалет, страшно",
            history=[],
            dossier_summary="пусто",
        )

    assert isinstance(report, PerceptionReport)
    assert report.risk_level == "elevated"
    assert report.dominant_emotion == "страх"
    assert "relationships/school_peers" in report.folder_hints


async def test_analyze_strips_markdown_wrapper(valid_json_text):
    """LLM иногда оборачивает JSON в ```json ...```. Анализатор это снимает."""
    wrapped = f"```json\n{valid_json_text}\n```"
    analyzer = MessageAnalyzer()
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm_response(wrapped)),
    ):
        report = await analyzer.analyze(
            current_message="x", history=[], dossier_summary="пусто",
        )

    assert report.risk_level == "elevated"


async def test_analyze_invalid_json_raises():
    """Если LLM вернул не-JSON — AnalyzerError."""
    analyzer = MessageAnalyzer()
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm_response("это не json, а просто текст")),
    ):
        with pytest.raises(AnalyzerError, match="JSON"):
            await analyzer.analyze(
                current_message="x", history=[], dossier_summary="пусто",
            )


async def test_analyze_invalid_schema_raises():
    """Если JSON есть, но не соответствует схеме — AnalyzerError."""
    bad = json.dumps({"risk_level": "wrong", "dominant_emotion": "x"})
    analyzer = MessageAnalyzer()
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm_response(bad)),
    ):
        with pytest.raises(AnalyzerError):
            await analyzer.analyze(
                current_message="x", history=[], dossier_summary="пусто",
            )


async def test_analyze_llm_error_propagates():
    """Если LLM упал — исключение пробрасывается (НЕ глотаем)."""
    analyzer = MessageAnalyzer()
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(side_effect=RuntimeError("LLM недоступен")),
    ):
        with pytest.raises(RuntimeError, match="LLM"):
            await analyzer.analyze(
                current_message="x", history=[], dossier_summary="пусто",
            )
```

- [ ] **Шаг 2: Запустить тесты — упадут с ImportError**

```
cd backend && pytest tests/perception/test_analyzer.py -v
```

- [ ] **Шаг 3: Реализовать `backend/app/core/perception/analyzer.py`**

```python
"""MessageAnalyzer — отдельный LLM-вызов на каждое сообщение.

Дизайн: §5 в spec.

Поведение:
- Получает текущее сообщение, историю и выжимку досье.
- Делает один LLM-вызов с системным промптом (analyzer_prompt.py).
- Парсит JSON-ответ в PerceptionReport.
- Не глотает исключения LLM (по дизайн-решению §9: упало — упало,
  основной поток разберётся).

НЕ хранит состояния. Один и тот же экземпляр можно вызывать конкурентно.
"""

from __future__ import annotations

import json
import logging
import re

from pydantic import ValidationError

from app.core.llm.base import Message
from app.core.llm.factory import get_provider
from app.core.perception.analyzer_prompt import (
    ANALYZER_SYSTEM_PROMPT,
    build_analyzer_user_prompt,
)
from app.core.perception.types import PerceptionReport

logger = logging.getLogger(__name__)


class AnalyzerError(Exception):
    """Ошибка парсинга или валидации ответа анализатора."""


# Регулярка для снятия ```json ... ``` обёртки если LLM её добавил
_MARKDOWN_JSON_FENCE = re.compile(
    r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL,
)


def strip_markdown_fence(text: str) -> str:
    """Снять ```json ... ``` обёртку, если есть.

    Public helper — переиспользуется в ReflectionAgent для парсинга JSON.
    """
    text = text.strip()
    m = _MARKDOWN_JSON_FENCE.match(text)
    if m:
        return m.group(1).strip()
    return text


class MessageAnalyzer:
    """Анализатор сообщений. См. spec §5."""

    def __init__(self, *, temperature: float = 0.3, max_tokens: int = 800):
        # Невысокая температура — нам нужны стабильные структурированные ответы.
        # max_tokens с запасом на JSON + inner_monologue.
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def analyze(
        self,
        *,
        current_message: str,
        history: list[dict[str, str]],
        dossier_summary: str,
    ) -> PerceptionReport:
        """Проанализировать одно сообщение пользователя.

        Args:
            current_message: текст текущего сообщения.
            history: список последних реплик [{"role": "user|assistant", "content": "..."}].
            dossier_summary: текстовая выжимка досье (или "пусто").

        Returns:
            PerceptionReport.

        Raises:
            AnalyzerError: если LLM вернул невалидный JSON / схему.
            Прочие исключения LLM — пробрасываются как есть.
        """
        provider = get_provider()
        user_prompt = build_analyzer_user_prompt(
            current_message=current_message,
            history=history,
            dossier_summary=dossier_summary,
        )

        messages = [
            Message(role="system", content=ANALYZER_SYSTEM_PROMPT),
            Message(role="user", content=user_prompt),
        ]

        response = await provider.generate(
            messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )

        # 1. Снять markdown-обёртку если есть
        raw = strip_markdown_fence(response.text)

        # 2. Распарсить JSON
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning(
                "Analyzer returned non-JSON: %r (preview: %s)", e, raw[:200],
            )
            raise AnalyzerError(f"Не удалось распарсить JSON анализатора: {e}") from e

        # 3. Валидировать через Pydantic
        try:
            report = PerceptionReport(**data)
        except ValidationError as e:
            logger.warning(
                "Analyzer JSON failed schema validation: %s (data: %s)",
                e, data,
            )
            raise AnalyzerError(
                f"JSON анализатора не соответствует схеме: {e}",
            ) from e

        return report
```

- [ ] **Шаг 4: Запустить тесты — должны пройти**

```
cd backend && pytest tests/perception/test_analyzer.py -v
```

Ожидаемый результат: `5 passed`.

- [ ] **Шаг 5: Коммит**

```
git add backend/app/core/perception/analyzer.py backend/tests/perception/test_analyzer.py
git commit -m "feat(perception): MessageAnalyzer with JSON parsing and schema validation"
```

---

### Checkpoint Фазы 2

- [ ] `pytest tests/perception/test_types.py tests/perception/test_analyzer.py -v` — всё зелёное.
- [ ] `MessageAnalyzer.analyze()` работает (по моку), возвращает валидный `PerceptionReport`.
- [ ] Все коммиты на месте.

---

## Фаза 3: Mood

**Цель:** реализовать сервис над Redis, который хранит и обновляет MoodState. Формулы обновления — простые функции от PerceptionReport.

### Задача 3.1: Redis-обёртка для MoodState

**Файлы:**
- Create: `backend/app/core/perception/mood.py`
- Test: `backend/tests/perception/test_mood.py`

- [ ] **Шаг 1: Написать тест `backend/tests/perception/test_mood.py`**

Подсказка: для тестов используем `fakeredis` чтобы не зависеть от настоящего Redis. Если `fakeredis` ещё не установлен — добавим в dev.

```python
"""Тесты MoodService.

Используем fakeredis вместо настоящего Redis (быстро, изолированно, нет I/O).
"""

from __future__ import annotations

import pytest
import pytest_asyncio
import fakeredis.aioredis as fakeredis

from app.core.perception.mood import MoodService
from app.core.perception.types import MoodState, PerceptionReport


@pytest_asyncio.fixture
async def fake_redis():
    """Чистый fakeredis на каждый тест."""
    r = fakeredis.FakeRedis()
    yield r
    await r.aclose()


@pytest_asyncio.fixture
async def mood_service(fake_redis):
    return MoodService(redis_client=fake_redis)


def _report(risk: str = "normal", emotion: str = "нейтрально", trust: float = 0.7) -> PerceptionReport:
    return PerceptionReport(
        risk_level=risk,
        dominant_emotion=emotion,
        secondary_emotions=[],
        theme="general",
        hidden_signals=[],
        open_questions=[],
        what_user_needs="x",
        trust_level=trust,
        folder_hints=[],
        inner_monologue="x",
    )


async def test_get_returns_default_for_new_session(mood_service):
    """Если ключа нет в Redis — возвращаем дефолт."""
    mood = await mood_service.get("session-1")
    assert mood == MoodState.default()


async def test_set_and_get_roundtrip(mood_service):
    custom = MoodState(alertness=0.9, warmth=0.5, pace=0.3, assertiveness=0.7,
                       trust_in_user=0.8, depth=0.6)
    await mood_service.set("session-1", custom)
    got = await mood_service.get("session-1")
    assert got == custom


async def test_update_immediate_risk_pushes_alertness(mood_service):
    """risk_level=immediate → alertness устремляется к 1.0."""
    initial = await mood_service.get("session-1")
    assert initial.alertness < 0.5

    new_state = await mood_service.update_from_report(
        "session-1", _report(risk="immediate"),
    )
    assert new_state.alertness >= 0.85


async def test_update_normal_risk_decays_alertness(mood_service):
    """При normal risk alertness постепенно затухает (× 0.7)."""
    high = MoodState(alertness=0.9, warmth=0.7, pace=0.5,
                     assertiveness=0.5, trust_in_user=0.7, depth=0.5)
    await mood_service.set("session-1", high)

    new_state = await mood_service.update_from_report(
        "session-1", _report(risk="normal"),
    )
    assert new_state.alertness < high.alertness


async def test_update_high_risk_slows_pace(mood_service):
    new_state = await mood_service.update_from_report(
        "session-2", _report(risk="high"),
    )
    assert new_state.pace < 0.5
    assert new_state.warmth >= 0.7


async def test_clear_removes_session_state(mood_service):
    await mood_service.set("session-1", MoodState(
        alertness=0.9, warmth=0.5, pace=0.5, assertiveness=0.5,
        trust_in_user=0.5, depth=0.5,
    ))
    await mood_service.clear("session-1")
    got = await mood_service.get("session-1")
    assert got == MoodState.default()
```

- [ ] **Шаг 2: Добавить fakeredis в dev-зависимости**

В `backend/pyproject.toml` секция `[project.optional-dependencies] dev = [...]`, добавить:
```toml
    "fakeredis>=2.26.0",
```

И установить:
```
pip install -e ".[dev]"
```

- [ ] **Шаг 3: Запустить тесты — упадут с ImportError**

```
cd backend && pytest tests/perception/test_mood.py -v
```

- [ ] **Шаг 4: Реализовать `backend/app/core/perception/mood.py`**

```python
"""MoodService — Redis-обёртка над MoodState с правилами обновления.

Дизайн: §6 в spec.

Хранение:
- Ключ: mood:{session_id}
- Значение: JSON-сериализация MoodState
- TTL: 24 часа после последнего обновления

Обновление: чистые функции от PerceptionReport. Без LLM.
"""

from __future__ import annotations

import json
import logging
from typing import Protocol

from app.core.perception.types import MoodState, PerceptionReport

logger = logging.getLogger(__name__)


# Через сколько секунд протухает Mood без активности
MOOD_TTL_SECONDS = 24 * 60 * 60


class _RedisLike(Protocol):
    """Минимальный интерфейс Redis-клиента.

    Реальный — redis.asyncio.Redis. В тестах — fakeredis.
    """

    async def get(self, key: str) -> bytes | None: ...
    async def set(self, key: str, value: str, ex: int | None = None) -> bool: ...
    async def delete(self, *keys: str) -> int: ...


def _key(session_id: str) -> str:
    return f"mood:{session_id}"


# ============================================================================
# Формулы обновления
# ============================================================================


def _risk_to_alertness(risk: str) -> float:
    return {
        "normal": 0.2,
        "elevated": 0.55,
        "high": 0.85,
        "immediate": 0.98,
    }.get(risk, 0.3)


def _risk_to_pace(risk: str) -> float:
    """При высоком риске темп замедляется."""
    return {
        "normal": 0.5,
        "elevated": 0.4,
        "high": 0.25,
        "immediate": 0.15,
    }.get(risk, 0.5)


def _risk_to_warmth_floor(risk: str) -> float:
    """При высоком риске нужно больше тепла, не меньше."""
    return {
        "normal": 0.55,
        "elevated": 0.7,
        "high": 0.85,
        "immediate": 0.95,
    }.get(risk, 0.6)


def _emotion_warmth_delta(emotion: str) -> float:
    """Эмоция даёт небольшую коррекцию warmth."""
    e = emotion.lower()
    if any(w in e for w in ["страх", "горе", "печаль", "одиноч", "беспомощ", "отчаян"]):
        return +0.1
    if any(w in e for w in ["злость", "гнев", "ярость"]):
        return -0.05
    return 0.0


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def compute_next_mood(prev: MoodState, report: PerceptionReport) -> MoodState:
    """Рассчитать новое состояние Mood по предыдущему + отчёту.

    Чистая функция, без I/O — удобно тестировать.
    """
    target_alertness = _risk_to_alertness(report.risk_level)
    # Alertness реагирует быстро (растёт), но затухает плавно
    if target_alertness > prev.alertness:
        new_alertness = target_alertness
    else:
        new_alertness = max(prev.alertness * 0.7, target_alertness)

    target_warmth_floor = _risk_to_warmth_floor(report.risk_level)
    new_warmth = _clamp(
        max(prev.warmth + _emotion_warmth_delta(report.dominant_emotion), target_warmth_floor),
        lo=0.3, hi=1.0,
    )

    new_pace = _risk_to_pace(report.risk_level)

    # Assertiveness — следует за trust (если пользователь открыт, можно вести),
    # но при immediate всегда низкая (не давить).
    if report.risk_level == "immediate":
        new_assertiveness = 0.2
    else:
        new_assertiveness = _clamp(0.3 + 0.4 * report.trust_level)

    # Trust_in_user — наследуем trust_level, сглаживаем
    new_trust = _clamp(0.5 * prev.trust_in_user + 0.5 * report.trust_level)

    # Depth — высокий trust + низкий риск = можно глубже
    if report.risk_level in ("high", "immediate"):
        new_depth = 0.4  # фокус на стабилизации, не на глубине
    else:
        new_depth = _clamp(0.3 + 0.6 * report.trust_level)

    return MoodState(
        alertness=new_alertness,
        warmth=new_warmth,
        pace=new_pace,
        assertiveness=new_assertiveness,
        trust_in_user=new_trust,
        depth=new_depth,
    )


# ============================================================================
# Сервис
# ============================================================================


class MoodService:
    """Сервис над Redis для хранения/обновления MoodState.

    Принимает Redis-клиент в конструктор — это упрощает тесты (fakeredis).
    """

    def __init__(self, redis_client: _RedisLike):
        self._redis = redis_client

    async def get(self, session_id: str) -> MoodState:
        """Получить текущее настроение или дефолт, если ключа нет."""
        raw = await self._redis.get(_key(session_id))
        if raw is None:
            return MoodState.default()
        try:
            data = json.loads(raw)
            return MoodState(**data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(
                "Corrupted mood state for session=%s: %s. Returning default.",
                session_id, e,
            )
            return MoodState.default()

    async def set(self, session_id: str, mood: MoodState) -> None:
        """Сохранить настроение с TTL."""
        await self._redis.set(
            _key(session_id),
            mood.model_dump_json(),
            ex=MOOD_TTL_SECONDS,
        )

    async def update_from_report(
        self,
        session_id: str,
        report: PerceptionReport,
    ) -> MoodState:
        """Прочитать текущее, применить правила, сохранить, вернуть новое."""
        prev = await self.get(session_id)
        new = compute_next_mood(prev, report)
        await self.set(session_id, new)
        return new

    async def clear(self, session_id: str) -> None:
        """Удалить состояние сессии (для тестов / выхода пользователя)."""
        await self._redis.delete(_key(session_id))
```

- [ ] **Шаг 5: Запустить тесты — должны пройти**

```
cd backend && pytest tests/perception/test_mood.py -v
```

Ожидаемый результат: `6 passed`.

- [ ] **Шаг 6: Коммит**

```
git add backend/pyproject.toml backend/app/core/perception/mood.py backend/tests/perception/test_mood.py
git commit -m "feat(perception): MoodService with redis storage and update rules"
```

---

### Задача 3.2: Redis-зависимость для FastAPI

**Файлы:**
- Create: `backend/app/core/perception/redis_client.py`
- Modify: `backend/app/main.py` (добавить инициализацию в lifespan)

- [ ] **Шаг 1: Создать `backend/app/core/perception/redis_client.py`**

```python
"""Глобальный async Redis-клиент для слоя восприятия.

Создаётся один раз при старте приложения, закрывается при shutdown.
Используется и для Mood, и для отложенного запуска ReflectionAgent (Фаза 5).
"""

from __future__ import annotations

import logging

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """Вернуть singleton Redis-клиент.

    Создаётся при первом обращении. Не закрывает сам себя — закрытие
    через close_redis() в lifespan.
    """
    global _client
    if _client is None:
        _client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=False,  # MoodService и так делает json.loads
        )
        logger.info("Redis client created: %s", settings.redis_url)
    return _client


async def close_redis() -> None:
    """Закрыть пул соединений Redis. Вызывается в lifespan на shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("Redis client closed")
```

- [ ] **Шаг 2: Подключить к lifespan в `backend/app/main.py`**

Открой `backend/app/main.py`. В `lifespan()` найди раздел shutdown (после `yield`). Добавь до `await dispose_engine()`:

```python
    # 0. Redis (слой восприятия)
    from app.core.perception.redis_client import close_redis
    try:
        await close_redis()
    except Exception:
        logger.exception("Error closing Redis")
```

- [ ] **Шаг 3: Запустить uvicorn и проверить что Redis инициализируется**

```
cd backend && uvicorn app.main:app --reload --port 8001
```

В логах при первом запросе к будущему /api/chat (или просто `/api/health`) → должно быть `Redis client created: redis://...`.

Ctrl+C → должно быть `Redis client closed`.

- [ ] **Шаг 4: Коммит**

```
git add backend/app/core/perception/redis_client.py backend/app/main.py
git commit -m "feat(perception): redis singleton client with lifespan integration"
```

---

### Checkpoint Фазы 3

- [ ] `pytest tests/perception/test_mood.py -v` — все зелёные.
- [ ] `redis-cli ping` отвечает `PONG`, и при старте uvicorn в логах появляется создание Redis-клиента.
- [ ] При корректном завершении uvicorn (Ctrl+C) Redis закрывается без ошибок.

---

## Фаза 4: PromptBuilder и новый чат-эндпоинт под флагом

**Цель:** связать всё вместе — анализатор + mood + досье + сборка промпта основной LLM. Старый `chat.py` НЕ трогаем; флаг `settings.use_perception_layer` переключает между старым и новым обработчиком.

### Задача 4.1: Сборка выжимки досье в текст

**Файлы:**
- Create: `backend/app/core/perception/dossier_summary.py`
- Test: `backend/tests/perception/test_dossier_summary.py`

- [ ] **Шаг 1: Написать тест `backend/tests/perception/test_dossier_summary.py`**

```python
"""Тесты сборки текстовой выжимки досье для промптов."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.perception.dossier_summary import (
    facts_to_compact_summary,
    facts_to_full_dossier_block,
)
from app.data.dossier_models import DossierFact, DossierQuote


def _fact(folder, subfolder, summary, severity=0.5, tags=None) -> DossierFact:
    """Создать DossierFact в памяти (без БД) для теста."""
    f = DossierFact(
        id="fact-1",
        user_id="user-1",
        folder=folder,
        subfolder=subfolder,
        summary=summary,
        tags=tags or [],
        severity=severity,
        confidence=0.8,
        first_mentioned=datetime.now(timezone.utc),
        last_mentioned=datetime.now(timezone.utc),
        times_mentioned=1,
        source_session_ids=[],
        source_message_ids=[],
        superseded_by=None,
    )
    f.quotes = []
    return f


def test_compact_summary_empty_returns_placeholder():
    s = facts_to_compact_summary([])
    assert "пусто" in s.lower() or "нет" in s.lower()


def test_compact_summary_lists_facts():
    facts = [
        _fact("family", "parents", "Папа пьёт", severity=0.95),
        _fact("relationships", "school_peers", "Травля в школе", severity=0.8),
    ]
    s = facts_to_compact_summary(facts)
    assert "Папа пьёт" in s
    assert "Травля" in s
    assert "family/parents" in s


def test_full_block_includes_quotes():
    f = _fact("family", "parents", "Папа пьёт", severity=0.95)
    f.quotes = [
        DossierQuote(
            id="q-1", fact_id=f.id,
            text="вчера папа опять напился",
            session_id="s-1", message_id="m-1",
            created_at=datetime.now(timezone.utc),
        ),
    ]
    block = facts_to_full_dossier_block([f])
    assert "Папа пьёт" in block
    assert "вчера папа опять напился" in block
```

- [ ] **Шаг 2: Запустить тесты — упадут**

```
cd backend && pytest tests/perception/test_dossier_summary.py -v
```

- [ ] **Шаг 3: Реализовать `backend/app/core/perception/dossier_summary.py`**

```python
"""Сериализация фактов досье в текст для промптов LLM.

Два варианта:
- compact_summary — короткая выжимка для МессагеAnalyzer
  (он использует это чтобы понять «кто это»).
- full_dossier_block — полный блок для основной LLM
  (с цитатами, чтобы Кайрос мог ссылаться на конкретные слова).
"""

from __future__ import annotations

from app.data.dossier_models import DossierFact


def facts_to_compact_summary(facts: list[DossierFact]) -> str:
    """Короткая выжимка: одна строка на факт.

    Формат:
        - [folder/subfolder, sev=0.95] Папа пьёт
        - [relationships/school_peers, sev=0.80] Травля в школе

    Если фактов нет — «пусто».
    """
    if not facts:
        return "(пусто — досье ещё не наполнено)"

    lines = []
    for f in facts:
        loc = f"{f.folder}/{f.subfolder}" if f.subfolder else f.folder
        lines.append(f"- [{loc}, sev={f.severity:.2f}] {f.summary}")
    return "\n".join(lines)


def facts_to_full_dossier_block(facts: list[DossierFact]) -> str:
    """Полный блок с цитатами для основной LLM.

    Формат:
        ## ЧТО Я ЗНАЮ О НЁМ/НЕЙ

        ### family/parents — Папа пьёт (severity 0.95, упомянуто 3 раза)
        Цитаты:
        - «вчера папа опять напился»
        - «когда отец бухой я прячусь»

        ### relationships/school_peers — ...

    Если фактов нет — пустая строка.
    """
    if not facts:
        return ""

    parts = ["## ЧТО Я ЗНАЮ О НЁМ/НЕЙ\n"]
    for f in facts:
        loc = f"{f.folder}/{f.subfolder}" if f.subfolder else f.folder
        parts.append(
            f"### {loc} — {f.summary} "
            f"(severity {f.severity:.2f}, упомянуто {f.times_mentioned} раз)"
        )
        if f.quotes:
            parts.append("Цитаты:")
            for q in f.quotes[-3:]:  # последние 3 цитаты, не все
                parts.append(f"- «{q.text}»")
        parts.append("")  # пустая строка между фактами

    return "\n".join(parts)
```

- [ ] **Шаг 4: Запустить тесты — должны пройти**

```
cd backend && pytest tests/perception/test_dossier_summary.py -v
```

- [ ] **Шаг 5: Коммит**

```
git add backend/app/core/perception/dossier_summary.py backend/tests/perception/test_dossier_summary.py
git commit -m "feat(perception): dossier facts → text summary serialization"
```

---

### Задача 4.2: PromptBuilder для основной LLM

**Файлы:**
- Create: `backend/app/core/perception/prompt_builder.py`
- Test: `backend/tests/perception/test_prompt_builder.py`

- [ ] **Шаг 1: Написать тест `backend/tests/perception/test_prompt_builder.py`**

```python
"""Тесты PromptBuilder — сборки финального промпта для основной LLM."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.perception.prompt_builder import build_main_prompt
from app.core.perception.types import MoodState, PerceptionReport
from app.data.dossier_models import DossierFact


def _report(risk="normal") -> PerceptionReport:
    return PerceptionReport(
        risk_level=risk,
        dominant_emotion="страх",
        secondary_emotions=["беспомощность"],
        theme="school_peers/bullying",
        hidden_signals=["возможно угрозу не озвучила"],
        open_questions=["что именно сказали"],
        what_user_needs="хочет, чтобы её услышали",
        trust_level=0.85,
        folder_hints=["relationships/school_peers"],
        inner_monologue="не торопить. она вернулась к этой теме.",
    )


def _mood() -> MoodState:
    return MoodState(
        alertness=0.8, warmth=0.95, pace=0.25,
        assertiveness=0.3, trust_in_user=0.85, depth=0.6,
    )


def _fact() -> DossierFact:
    f = DossierFact(
        id="f-1", user_id="u-1",
        folder="relationships", subfolder="school_peers",
        summary="Мальчики в классе угрожают",
        tags=["threat"],
        severity=0.9, confidence=0.85,
        first_mentioned=datetime.now(timezone.utc),
        last_mentioned=datetime.now(timezone.utc),
        times_mentioned=3,
        source_session_ids=[], source_message_ids=[],
        superseded_by=None,
    )
    f.quotes = []
    return f


def test_prompt_includes_mood_block():
    prompt = build_main_prompt(
        report=_report("elevated"),
        mood=_mood(),
        relevant_facts=[],
    )
    assert "ТЕКУЩЕЕ НАСТРОЕНИЕ" in prompt
    assert "alertness: 0.80" in prompt


def test_prompt_includes_dossier_when_facts_present():
    prompt = build_main_prompt(
        report=_report(),
        mood=_mood(),
        relevant_facts=[_fact()],
    )
    assert "ЧТО Я ЗНАЮ" in prompt
    assert "Мальчики в классе угрожают" in prompt


def test_prompt_excludes_dossier_block_when_empty():
    prompt = build_main_prompt(
        report=_report(),
        mood=_mood(),
        relevant_facts=[],
    )
    assert "ЧТО Я ЗНАЮ" not in prompt


def test_prompt_includes_inner_monologue_marked_internal():
    prompt = build_main_prompt(
        report=_report(),
        mood=_mood(),
        relevant_facts=[],
    )
    assert "не торопить" in prompt
    # Должен быть пометка что это внутренние мысли
    assert "ВНУТРЕННИЕ МЫСЛИ" in prompt or "ТВОИ МЫСЛИ" in prompt


def test_prompt_includes_base_kairos_prompt():
    """Базовый промпт Кайроса (роль, запреты) должен быть в финальном."""
    prompt = build_main_prompt(
        report=_report(),
        mood=_mood(),
        relevant_facts=[],
    )
    assert "Кайрос" in prompt
    assert "ЗАПРЕЩЁННЫЕ ФРАЗЫ" in prompt


def test_prompt_immediate_risk_includes_crisis_section():
    """При immediate риске должен быть кризисный блок."""
    prompt = build_main_prompt(
        report=_report("immediate"),
        mood=_mood(),
        relevant_facts=[],
    )
    # Соглашение о тексте кризисного блока — в base prompts.crisis
    assert "112" in prompt or "8-800" in prompt
```

- [ ] **Шаг 2: Запустить — упадут**

```
cd backend && pytest tests/perception/test_prompt_builder.py -v
```

- [ ] **Шаг 3: Реализовать `backend/app/core/perception/prompt_builder.py`**

```python
"""Сборка финального системного промпта для основной LLM.

Входы:
- PerceptionReport (от MessageAnalyzer)
- MoodState (текущее настроение)
- Релевантные факты досье

Выход: единая большая строка system_prompt.

Что внутри:
- Базовый Кайрос (роль, запреты, стиль речи) — из app.core.prompts.base
- Кризисный блок (если risk_level != normal) — из app.core.prompts.crisis
- Блок Mood (текстовый)
- Блок «что я знаю» (если факты есть)
- Блок «что я только что заметил» (inner_monologue из отчёта)

Заметка: терапевтические протоколы SIX C's / WHO PFA здесь НЕ
включаются явно как раньше (через branch_a/branch_b). Кайрос имеет к
ним доступ через ссылку в base промпте, и применяет их по обстановке,
опираясь на mood и what_user_needs.
"""

from __future__ import annotations

from app.core.prompts.base import PROMPT as BASE_PROMPT
from app.core.prompts.crisis import CRISIS_PROMPTS
from app.core.perception.dossier_summary import facts_to_full_dossier_block
from app.core.perception.types import MoodState, PerceptionReport
from app.data.dossier_models import DossierFact


def build_main_prompt(
    *,
    report: PerceptionReport,
    mood: MoodState,
    relevant_facts: list[DossierFact],
) -> str:
    """Собрать системный промпт для основной LLM.

    Args:
        report: результат MessageAnalyzer.
        mood: текущее настроение.
        relevant_facts: факты, отобранные по report.folder_hints.

    Returns:
        Полная строка system prompt.
    """
    parts: list[str] = [BASE_PROMPT]

    # Кризисный блок при не-normal риске
    crisis_block = CRISIS_PROMPTS.get(report.risk_level)
    if crisis_block:
        parts.append(crisis_block)

    # Блок настроения
    parts.append(mood.to_prompt_block())

    # Блок «что я знаю» (только если есть факты)
    dossier_block = facts_to_full_dossier_block(relevant_facts)
    if dossier_block:
        parts.append(dossier_block)

    # Блок «внутренних мыслей»
    parts.append(
        "## ТВОИ ВНУТРЕННИЕ МЫСЛИ (только для тебя, НЕ озвучивать пользователю)\n"
        f"{report.inner_monologue}"
    )

    # Блок «что нужно пользователю»
    parts.append(
        "## ЧТО НУЖНО ПОЛЬЗОВАТЕЛЮ СЕЙЧАС\n"
        f"{report.what_user_needs}"
    )

    return "\n\n".join(parts)
```

- [ ] **Шаг 4: Запустить тесты — пройдут**

```
cd backend && pytest tests/perception/test_prompt_builder.py -v
```

Ожидаемый результат: `6 passed`.

- [ ] **Шаг 5: Коммит**

```
git add backend/app/core/perception/prompt_builder.py backend/tests/perception/test_prompt_builder.py
git commit -m "feat(perception): main LLM prompt builder (mood + dossier + monologue)"
```

---

### Задача 4.3: PerceptionPipeline — оркестратор одного запроса

**Файлы:**
- Create: `backend/app/core/perception/pipeline.py`
- Test: `backend/tests/perception/test_pipeline.py`

- [ ] **Шаг 1: Написать тест `backend/tests/perception/test_pipeline.py`**

```python
"""Тесты PerceptionPipeline — оркестратора всего цикла одного сообщения.

Здесь критично: проверяем последовательность вызовов и правильное
использование результатов между компонентами.
"""

from __future__ import annotations

import json
import os
import pytest
import pytest_asyncio
import fakeredis.aioredis as fakeredis
from unittest.mock import AsyncMock, patch
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_pipeline.db"
os.environ["LLM_API_KEY"] = "test-key"

from app.core.llm.base import LLMResponse, UsageStats
from app.core.perception.pipeline import PerceptionPipeline, PipelineResult
from app.data.database import create_all_tables, drop_all_tables, async_session_factory
from app.data.models import User, ChatSession


@pytest_asyncio.fixture
async def db_with_user():
    await drop_all_tables()
    await create_all_tables()
    async with async_session_factory() as db:
        user = User(id=str(uuid4()), email="t@e.com")
        db.add(user)
        session = ChatSession(id=str(uuid4()), user_id=user.id)
        db.add(session)
        await db.commit()
        yield {"user_id": user.id, "session_id": session.id}
    await drop_all_tables()


@pytest_asyncio.fixture
async def fake_redis():
    r = fakeredis.FakeRedis()
    yield r
    await r.aclose()


def _llm(text: str, p_in=100, p_out=50) -> LLMResponse:
    return LLMResponse(
        text=text,
        usage=UsageStats(prompt_tokens=p_in, completion_tokens=p_out, total_tokens=p_in + p_out),
        response_time_ms=42.0,
    )


def _analyzer_response_json():
    return json.dumps({
        "risk_level": "elevated",
        "dominant_emotion": "страх",
        "secondary_emotions": [],
        "theme": "school_peers/bullying",
        "hidden_signals": [],
        "open_questions": [],
        "what_user_needs": "выслушать",
        "trust_level": 0.85,
        "folder_hints": [],
        "inner_monologue": "не торопить",
    }, ensure_ascii=False)


async def test_pipeline_full_cycle(db_with_user, fake_redis):
    """Полный цикл: analyzer → mood update → prompt build → main LLM."""

    # Двухступенчатый мок: первый вызов LLM = анализатор, второй = основной ответ
    call_count = {"n": 0}

    async def fake_generate(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _llm(_analyzer_response_json())
        return _llm("слышу тебя, расскажи подробнее")

    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(side_effect=fake_generate),
    ):
        async with async_session_factory() as db:
            pipeline = PerceptionPipeline(db=db, redis_client=fake_redis)
            result: PipelineResult = await pipeline.process_message(
                user_id=db_with_user["user_id"],
                session_id=db_with_user["session_id"],
                user_message="опять туалет, страшно",
                history=[],
            )

    assert call_count["n"] == 2  # один на анализатор, один на основной ответ
    assert result.report.risk_level == "elevated"
    assert "слышу тебя" in result.reply
    assert result.mood.alertness > 0.5  # mood обновился по elevated risk


async def test_pipeline_analyzer_failure_propagates(db_with_user, fake_redis):
    """Если анализатор упал — основной ответ не должен генерироваться."""
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(side_effect=RuntimeError("LLM down")),
    ):
        async with async_session_factory() as db:
            pipeline = PerceptionPipeline(db=db, redis_client=fake_redis)
            with pytest.raises(RuntimeError):
                await pipeline.process_message(
                    user_id=db_with_user["user_id"],
                    session_id=db_with_user["session_id"],
                    user_message="привет",
                    history=[],
                )
```

- [ ] **Шаг 2: Запустить — упадут с ImportError**

```
cd backend && pytest tests/perception/test_pipeline.py -v
```

- [ ] **Шаг 3: Реализовать `backend/app/core/perception/pipeline.py`**

```python
"""PerceptionPipeline — оркестратор одного цикла обработки сообщения.

Дизайн: §8 в spec.

Последовательность:
1. Загрузить контекст: история + выжимка досье + текущий mood
2. Вызвать MessageAnalyzer → PerceptionReport
3. Обновить Mood по отчёту
4. Подтянуть факты по folder_hints
5. Собрать main prompt
6. Вызвать основную LLM → reply
7. Вернуть PipelineResult со всеми артефактами

Этот класс НЕ пишет в БД (это работа chat.py — он создаёт Message-записи).
PerceptionPipeline только читает досье и обновляет Mood (Redis).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm.base import Message
from app.core.llm.factory import get_provider
from app.core.perception.analyzer import MessageAnalyzer
from app.core.perception.dossier import DossierService
from app.core.perception.dossier_summary import facts_to_compact_summary
from app.core.perception.mood import MoodService
from app.core.perception.prompt_builder import build_main_prompt
from app.core.perception.types import MoodState, PerceptionReport

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Результат полного цикла. Используется в chat.py для записи в БД."""

    report: PerceptionReport
    mood: MoodState
    reply: str
    response_time_ms: int | None
    prompt_tokens: int | None
    completion_tokens: int | None


class PerceptionPipeline:
    """Оркестратор одного цикла обработки сообщения.

    Stateless: создаётся per-request, принимая db + redis в конструктор.
    """

    def __init__(
        self,
        *,
        db: AsyncSession,
        redis_client,
        analyzer: MessageAnalyzer | None = None,
    ):
        self._db = db
        self._dossier = DossierService(db)
        self._mood = MoodService(redis_client)
        self._analyzer = analyzer or MessageAnalyzer()

    async def process_message(
        self,
        *,
        user_id: str | None,
        session_id: str,
        user_message: str,
        history: list[dict[str, str]],
    ) -> PipelineResult:
        """Полный цикл одного сообщения.

        Args:
            user_id: id пользователя (None для гостя).
            session_id: id сессии.
            user_message: текст текущего сообщения.
            history: предыдущие реплики [{"role", "content"}, ...].

        Returns:
            PipelineResult.

        Raises:
            AnalyzerError: если анализатор не смог распарсить ответ.
            httpx.HTTPError: если LLM упал.
        """
        # === Шаг 1: Контекст для анализатора ===
        # Если user_id None (гость) — досье пусто.
        if user_id:
            top_facts = await self._dossier.top_relevant_facts(user_id, limit=5)
            dossier_summary = facts_to_compact_summary(top_facts)
        else:
            top_facts = []
            dossier_summary = "(пользователь — гость, досье недоступно)"

        # === Шаг 2: Анализатор ===
        report = await self._analyzer.analyze(
            current_message=user_message,
            history=history,
            dossier_summary=dossier_summary,
        )
        logger.info(
            "Perception: session=%s risk=%s emotion=%s theme=%s",
            session_id[:8], report.risk_level,
            report.dominant_emotion, report.theme,
        )

        # === Шаг 3: Обновить Mood ===
        mood = await self._mood.update_from_report(session_id, report)

        # === Шаг 4: Подтянуть релевантные факты по hints ===
        relevant_facts = []
        if user_id and report.folder_hints:
            # Извлекаем уникальные top-level папки из folder_hints
            # (формат "folder/subfolder")
            target_folders = list({h.split("/")[0] for h in report.folder_hints})
            relevant_facts = await self._dossier.get_facts_by_folders(
                user_id, folders=target_folders,
            )
            # Если ничего не нашли — берём топ
            if not relevant_facts and top_facts:
                relevant_facts = top_facts

        # === Шаг 5: Собрать main prompt ===
        system_prompt = build_main_prompt(
            report=report,
            mood=mood,
            relevant_facts=relevant_facts,
        )

        # === Шаг 6: Вызвать основную LLM ===
        provider = get_provider()
        messages = [Message(role="system", content=system_prompt)]
        for h in history:
            messages.append(Message(role=h["role"], content=h["content"]))
        messages.append(Message(role="user", content=user_message))

        response = await provider.generate(messages)

        # === Шаг 7: Собрать результат ===
        return PipelineResult(
            report=report,
            mood=mood,
            reply=response.text,
            response_time_ms=int(response.response_time_ms),
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
        )
```

- [ ] **Шаг 4: Запустить тесты — пройдут**

```
cd backend && pytest tests/perception/test_pipeline.py -v
```

Ожидаемый результат: `2 passed`.

- [ ] **Шаг 5: Коммит**

```
git add backend/app/core/perception/pipeline.py backend/tests/perception/test_pipeline.py
git commit -m "feat(perception): PerceptionPipeline orchestrating full message cycle"
```

---

### Задача 4.4: Подключить PerceptionPipeline в `/api/chat` под флагом

**Файлы:**
- Modify: `backend/app/api/chat.py`
- Modify: `backend/app/data/models.py` (добавить поле `messages.perception_json`)
- Create: alembic-миграция для нового поля

- [ ] **Шаг 1: Добавить поле `perception_json` в модель Message**

В `backend/app/data/models.py` найди класс `Message`. После поля `completion_tokens` добавь:

```python
    # JSON-сериализация PerceptionReport (логирование для data flywheel + LoRA).
    # Заполняется только когда use_perception_layer=True.
    perception_json: Mapped[str | None] = mapped_column(Text, nullable=True)
```

- [ ] **Шаг 2: Сгенерировать и применить миграцию**

```
cd backend
alembic revision --autogenerate -m "add perception_json to messages"
alembic upgrade head
```

- [ ] **Шаг 3: Открыть `backend/app/api/chat.py`, найти эндпоинт `chat()`**

Нужно вставить разветвление на основе `settings.use_perception_layer` ПЕРЕД вызовом `_call_llm_with_fallback`. Найди блок начиная с `# === 6. Собрать промпт и историю для LLM ===`.

- [ ] **Шаг 4: Заменить блок 6-7 (старый промпт + LLM-вызов) на двухветочную логику**

Открой `backend/app/api/chat.py`. После блока «=== 5. Сохранить пользовательское сообщение ===» (`db.add(user_msg)`) и ПЕРЕД блоком «=== 6. Собрать промпт ... ===» вставь разветвление:

```python
    # === 6/7. Промпт + LLM (две ветки: новая или старая) ===
    if settings.use_perception_layer:
        # === НОВАЯ ВЕТКА: PerceptionPipeline ===
        from app.core.perception.pipeline import PerceptionPipeline
        from app.core.perception.redis_client import get_redis

        history_for_pipeline = [
            {"role": h.role, "content": h.content} for h in request.history
        ]

        try:
            pipeline = PerceptionPipeline(
                db=db,
                redis_client=get_redis(),
            )
            result = await pipeline.process_message(
                user_id=session.user_id,
                session_id=session.id,
                user_message=request.message,
                history=history_for_pipeline,
            )
            reply_text = result.reply
            metrics = {
                "response_time_ms": result.response_time_ms,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
            }
            # Логируем PerceptionReport для data flywheel
            user_msg.perception_json = result.report.model_dump_json()
            # ИЗ отчёта берём актуальный crisis_level (вместо assess_crisis_level)
            crisis_level = result.report.risk_level

        except Exception as e:
            logger.exception("Perception pipeline failed: %s", e)
            metrics = {"llm_error": f"perception_failed: {type(e).__name__}: {e}"}
            # Согласно дизайн-решению §9: rule-based fallback нет.
            # Честное сообщение пользователю.
            reply_text = (
                "Извини, я сейчас не могу отвечать. "
                "Если это срочно — нажми SOS вверху для номеров помощи."
            )
    else:
        # === СТАРАЯ ВЕТКА (существующая логика) ===
        system_prompt = build_system_prompt(
            branch=branch,
            crisis_level=crisis_level,
            use_router=False,
        )

        llm_messages: list[Message] = [Message(role="system", content=system_prompt)]
        for hist_msg in request.history:
            llm_messages.append(Message(role=hist_msg.role, content=hist_msg.content))
        llm_messages.append(Message(role="user", content=request.message))

        reply_text, metrics = await _call_llm_with_fallback(
            llm_messages=llm_messages,
            crisis_level=crisis_level,
        )
```

И УДАЛИ старый блок 6-7 ниже (от `system_prompt = build_system_prompt(...)` до конца `_call_llm_with_fallback(...)`), потому что теперь он внутри `else`.

- [ ] **Шаг 5: Проверить что старая ветка работает (флаг по умолчанию false)**

```
cd backend && uvicorn app.main:app --reload --port 8001
```

В другом терминале:
```
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "привет"}'
```

Должен прийти ответ как раньше (старая логика, перцепция выключена).

- [ ] **Шаг 6: Включить флаг и проверить новую ветку**

В `backend/.env` поставь:
```
USE_PERCEPTION_LAYER=true
```

Перезапусти uvicorn. Снова сделай curl. Должен прийти ответ — теперь через PerceptionPipeline. В логах должно быть:
```
Perception: session=... risk=... emotion=... theme=...
```

Если ответ нормальный — переключи флаг обратно на `false` (для безопасности на этом этапе).

- [ ] **Шаг 7: Добавить отдельный тест-файл для новой ветки**

Существующий `tests/test_chat.py` оставь как есть — он тестирует старую ветку (флаг false). Создай НОВЫЙ файл `backend/tests/test_chat_perception.py` для тестов новой ветки:

```python
"""Интеграционные тесты /api/chat при включённом use_perception_layer.

LLM мокается ДВАЖДЫ (анализатор + основной), потому что новая ветка
делает два последовательных вызова.
"""

from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
import fakeredis.aioredis as fakeredis
from httpx import ASGITransport, AsyncClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_chat_perception.db"
os.environ["LLM_API_KEY"] = "test-key"
os.environ["USE_PERCEPTION_LAYER"] = "true"

from app.core.llm.base import LLMResponse, UsageStats
from app.data.database import create_all_tables, drop_all_tables


def _llm(text: str) -> LLMResponse:
    return LLMResponse(
        text=text,
        usage=UsageStats(prompt_tokens=100, completion_tokens=50, total_tokens=150),
        response_time_ms=42.0,
    )


def _analyzer_json(risk: str = "normal") -> str:
    return json.dumps({
        "risk_level": risk,
        "dominant_emotion": "нейтрально",
        "secondary_emotions": [],
        "theme": "general",
        "hidden_signals": [],
        "open_questions": [],
        "what_user_needs": "выслушать",
        "trust_level": 0.7,
        "folder_hints": [],
        "inner_monologue": "ок",
    }, ensure_ascii=False)


@pytest_asyncio.fixture
async def app_with_db():
    await create_all_tables()
    from app.main import app
    yield app
    await drop_all_tables()


@pytest_asyncio.fixture
async def client(app_with_db, monkeypatch):
    # Подменяем get_redis на fakeredis-обёртку
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(
        "app.core.perception.redis_client.get_redis", lambda: fake,
    )
    transport = ASGITransport(app=app_with_db)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await fake.aclose()


async def _two_step_mock(analyzer_text: str, main_text: str):
    """Двухступенчатый мок: первый вызов = analyzer, второй = main."""
    calls = {"n": 0}
    async def gen(*args, **kwargs):
        calls["n"] += 1
        return _llm(analyzer_text if calls["n"] == 1 else main_text)
    return AsyncMock(side_effect=gen), calls


async def test_chat_normal_message_with_perception(client):
    """Обычное сообщение через PerceptionPipeline."""
    mock, calls = await _two_step_mock(
        _analyzer_json("normal"),
        "Слышу тебя. Расскажи, что у тебя сейчас.",
    )
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=mock,
    ):
        resp = await client.post("/api/chat", json={"message": "привет"})

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert calls["n"] == 2
    assert data["crisis_level"] == "normal"
    assert "Слышу тебя" in data["reply"]


async def test_chat_immediate_with_perception(client):
    """immediate из анализатора → crisis_contacts заполнены."""
    mock, _ = await _two_step_mock(
        _analyzer_json("immediate"),
        "Я слышу тебя. Это очень тяжело.",
    )
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=mock,
    ):
        resp = await client.post(
            "/api/chat",
            json={"message": "хочу умереть", "age_group": "adult"},
        )

    assert resp.status_code == 200
    assert resp.json()["crisis_level"] == "immediate"
    assert len(resp.json()["crisis_contacts"]) > 0
```

Старый `tests/test_chat.py` мы оставляем для проверки старой ветки до момента её удаления (Фаза 6).

- [ ] **Шаг 8: Запустить все тесты**

```
cd backend && pytest -v
```

Ожидаемый результат: всё зелёное. Если что-то падает в новой ветке — пофикси (скорее всего нужно мокать LLM двумя последовательными ответами как в `test_pipeline.py`).

- [ ] **Шаг 9: Коммит**

```
git add backend/app/data/models.py backend/alembic/versions/ backend/app/api/chat.py backend/tests/test_chat.py
git commit -m "feat(perception): wire PerceptionPipeline into /api/chat behind flag"
```

---

### Checkpoint Фазы 4

- [ ] При `USE_PERCEPTION_LAYER=false` старый чат работает как раньше.
- [ ] При `USE_PERCEPTION_LAYER=true` — отвечает через PerceptionPipeline (видно в логах).
- [ ] Поле `messages.perception_json` появляется в БД при включённом флаге.
- [ ] `pytest -v` — всё зелёное.

**Ручная проверка качества (важно сделать до Фазы 5):**
- [ ] Включи флаг, отправь *«опять эти уроды в туалет ходить страшно»* — Кайрос должен ответить иначе чем раньше: задавать уточняющий вопрос про контекст, а не просто «техника заземления 5-4-3-2-1».
- [ ] Отправь *«а они мне сказали кое-что...»* — старая ветка вернула бы `normal`, новая должна попросить пояснить, что именно сказали.
- [ ] Отправь *«хочу умереть»* — обе ветки должны дать кризисные контакты.

Если ручная проверка показывает, что новая ветка отвечает хуже — НЕ двигаемся в Фазу 5 пока не пофиксим промпт анализатора (это итеративная работа на реальном тексте).

---

## Фаза 5: ReflectionAgent через Celery

**Цель:** через 15 минут после последнего сообщения пользователя — фоновый Celery-таск читает все обработанные после чекпойнта сообщения и обновляет досье.

### Задача 5.1: Celery-приложение

**Файлы:**
- Create: `backend/app/celery_app.py`
- Create: `backend/celery_worker.py` (entry point для воркера)

- [ ] **Шаг 1: Создать `backend/app/celery_app.py`**

```python
"""Celery-приложение для фоновых задач (ReflectionAgent и др.).

Дизайн: §7 в spec.

Запуск воркера:
    cd backend
    celery -A app.celery_app worker -l info -Q reflection -c 1

(один воркер с concurrency=1 хватает для MVP, потом масштабируем).
"""

from __future__ import annotations

from celery import Celery

from app.config import settings


celery_app = Celery(
    "kairos",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.core.perception.reflection_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,

    # Очереди
    task_default_queue="default",
    task_routes={
        "app.core.perception.reflection_tasks.run_reflection": {"queue": "reflection"},
    },

    # Поведение задач
    task_acks_late=True,            # ack только после успеха (retry-friendly)
    task_reject_on_worker_lost=True,
    task_track_started=True,

    # Retry дефолты
    task_default_retry_delay=60,
    task_max_retries=3,

    # Result expiration
    result_expires=24 * 60 * 60,    # 24h
)
```

- [ ] **Шаг 2: Создать `backend/celery_worker.py` (точка входа)**

```python
"""Точка входа для Celery worker.

Запуск:
    cd backend
    celery -A celery_worker:celery_app worker -l info -Q reflection -c 1
"""

from app.celery_app import celery_app

# Импорт задач, чтобы они зарегистрировались в celery_app
from app.core.perception import reflection_tasks  # noqa: F401
```

- [ ] **Шаг 3: Коммит**

```
git add backend/app/celery_app.py backend/celery_worker.py
git commit -m "feat(perception): celery app and worker entry point"
```

---

### Задача 5.2: Промпт ReflectionAgent для извлечения фактов

**Файлы:**
- Create: `backend/app/core/perception/reflection_prompt.py`

- [ ] **Шаг 1: Создать `backend/app/core/perception/reflection_prompt.py`**

```python
"""Промпты для ReflectionAgent.

Два этапа имеют свои промпты:
- EXTRACT: извлечение фактов-кандидатов из необработанного хвоста разговора.
- DEDUPE: семантическое сравнение факта-кандидата с существующими.
"""

EXTRACT_SYSTEM_PROMPT = """\
Ты — рефлексирующий аналитик Кайроса. Ты НЕ отвечаешь пользователю.
Твоя задача — прочитать набор сообщений пользователя и извлечь \
устойчивые ФАКТЫ о его жизни, которые стоит запомнить надолго.

Что считать фактом:
- Конкретные обстоятельства (есть брат, переехал в Москву в 2024).
- Эмоционально значимые события (умер дедушка, развод родителей).
- Триггеры и ресурсы (туалет в школе пугает, подруга Маша поддерживает).
- Привычки и ритуалы (общается с Кайросом каждый день в 20:00).
- Ценности и цели.

Что НЕ считать фактом:
- Реакции на конкретное сообщение в моменте («сегодня грустно»).
- Технические артефакты («написал слово через опечатку»).
- Гипотезы Кайроса без подтверждения в речи пользователя.

ТЫ ОБЯЗАН:
1. Думать, а не сопоставлять подстроки. Если упомянут «братишка» — \
   значит у пользователя есть брат, и факт идёт в family/siblings.
2. Использовать английские snake_case имена папок и kebab-case тэги.
3. Сохранять буквальные цитаты пользователя — это доказательная база.
4. Если факт может попасть в несколько папок — выбрать одну, ОСНОВНУЮ.
5. Для пользовательских (custom) папок — давать осмысленное английское имя \
   (medical_visits, army_recruitment, не транскрипция).
6. Возвращать строго валидный JSON-массив. Без объяснений вне JSON.

Структура каждого факта в выходном JSON:
{
  "summary": str (1-2 предложения),
  "candidate_folder": str (одна из 14 верхнего уровня),
  "candidate_subfolder": str | null (имя подпапки или null если папка её не требует),
  "candidate_tags": [str, ...] (kebab-case, до 5),
  "severity": float (0.0-1.0),
  "confidence": float (0.0-1.0 — насколько ты уверен),
  "quotes": [
    {"message_id": str, "text": str (буквальная фраза пользователя)},
    ...
  ]
}

Верхнеуровневые папки (всегда из этого списка):
identity, childhood, family, relationships, work_school, losses, triggers, \
resources, values, health, crisis_history, goals, routines, custom.

Обязательные подпапки (где applicable):
- family: parents, siblings, grandparents, extended
- relationships: friends, romantic, school_peers, colleagues
- triggers: sensory, situational, relational
- health: body, sleep, illness, appearance, mental
- custom: ЛЮБОЕ английское snake_case имя

Если фактов нет — верни пустой массив [].
"""


def build_extract_user_prompt(
    *,
    messages_block: str,
    existing_dossier_summary: str,
) -> str:
    """Собрать user-prompt для extract.

    Args:
        messages_block: текстовый блок сообщений пользователя в хронологическом порядке
                        с message_id рядом с каждым.
        existing_dossier_summary: компактная выжимка существующего досье
                                  (чтобы агент не дублировал то, что уже есть).
    """
    return (
        f"## ТЕКУЩЕЕ ДОСЬЕ ПОЛЬЗОВАТЕЛЯ (для ориентира):\n"
        f"{existing_dossier_summary}\n\n"
        f"## НЕОБРАБОТАННЫЕ СООБЩЕНИЯ ПОЛЬЗОВАТЕЛЯ:\n"
        f"{messages_block}\n\n"
        f"Извлеки факты по схеме. Только JSON-массив."
    )


DEDUPE_SYSTEM_PROMPT = """\
Ты — рефлексирующий аналитик Кайроса. Тебе показан ОДИН факт-кандидат \
и список существующих фактов в той же папке.

Твоя задача — определить:
- Есть ли среди существующих факт, который семантически тот же (просто \
  переформулирован или дополнен)?
- Или это действительно новый факт, который нужно создать с нуля?
- Или это противоречит существующему (например, было «живёт с мамой», \
  стало «живёт с отцом») — тогда новый факт замещает старый.

Возможные решения (один из):
- "merge": слить с факт-id (тот же факт, добавить цитату)
- "create_new": создать новый факт
- "supersede": создать новый, пометить старый как устаревший

Верни строго валидный JSON:
{
  "decision": "merge" | "create_new" | "supersede",
  "target_fact_id": str | null  (id существующего факта для merge или supersede)
}
"""


def build_dedupe_user_prompt(
    *,
    candidate_summary: str,
    candidate_quotes: list[str],
    existing_facts: list[dict],
) -> str:
    """Собрать user-prompt для dedupe."""
    existing_block = "\n".join(
        f"- id={f['id']} sev={f['severity']:.2f} «{f['summary']}»"
        for f in existing_facts
    )
    quotes_block = "\n".join(f"  «{q}»" for q in candidate_quotes)
    return (
        f"## КАНДИДАТ:\n"
        f"summary: {candidate_summary}\n"
        f"quotes:\n{quotes_block}\n\n"
        f"## СУЩЕСТВУЮЩИЕ ФАКТЫ В ТОЙ ЖЕ ПАПКЕ:\n"
        f"{existing_block}\n\n"
        f"Верни JSON-решение."
    )
```

- [ ] **Шаг 2: Коммит**

```
git add backend/app/core/perception/reflection_prompt.py
git commit -m "feat(perception): reflection extract and dedupe prompts"
```

---

### Задача 5.3: ReflectionAgent — основная логика

**Файлы:**
- Create: `backend/app/core/perception/reflection_agent.py`
- Test: `backend/tests/perception/test_reflection_agent.py`

- [ ] **Шаг 1: Написать тест `backend/tests/perception/test_reflection_agent.py`**

```python
"""Тесты ReflectionAgent — полный цикл extract → classify → dedupe → update.

LLM замокан. Проверяем, что:
- Корректно загружаются сообщения после чекпойнта.
- Создаются факты с цитатами.
- При повторе — увеличивается times_mentioned.
- Чекпойнт сдвигается.
"""

from __future__ import annotations

import json
import os
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_reflection.db"
os.environ["LLM_API_KEY"] = "test-key"

from app.core.llm.base import LLMResponse, UsageStats
from app.core.perception.reflection_agent import ReflectionAgent
from app.data.database import create_all_tables, drop_all_tables, async_session_factory
from app.data.models import User, ChatSession, Message
from app.data.dossier_models import DossierFact, DossierCheckpoint


def _llm(text: str) -> LLMResponse:
    return LLMResponse(
        text=text,
        usage=UsageStats(prompt_tokens=200, completion_tokens=100, total_tokens=300),
        response_time_ms=100.0,
    )


@pytest_asyncio.fixture
async def db_with_messages():
    """Создаём пользователя, сессию и 3 сообщения. Чекпойнта НЕТ — это
    значит агент должен обработать всё с нуля."""
    await drop_all_tables()
    await create_all_tables()
    async with async_session_factory() as db:
        user = User(id=str(uuid4()), email="t@e.com")
        db.add(user)
        session = ChatSession(id=str(uuid4()), user_id=user.id)
        db.add(session)

        msg_ids = []
        for i, text in enumerate([
            "у меня есть младший братишка егор",
            "папа опять напился вчера",
            "я общаюсь с тобой каждый день в 20:00",
        ]):
            mid = str(uuid4())
            msg_ids.append(mid)
            db.add(Message(
                id=mid, session_id=session.id, role="user", content=text,
                server_timestamp=datetime.now(timezone.utc) + timedelta(seconds=i),
            ))
        await db.commit()
        yield {"user_id": user.id, "session_id": session.id, "msg_ids": msg_ids}
    await drop_all_tables()


def _extract_response_for_three_messages(msg_ids):
    """Мок-ответ extract-этапа для 3 сообщений."""
    return json.dumps([
        {
            "summary": "Есть младший брат Егор",
            "candidate_folder": "family",
            "candidate_subfolder": "siblings",
            "candidate_tags": ["younger-brother"],
            "severity": 0.3,
            "confidence": 0.95,
            "quotes": [{"message_id": msg_ids[0], "text": "у меня есть младший братишка егор"}],
        },
        {
            "summary": "Папа злоупотребляет алкоголем",
            "candidate_folder": "family",
            "candidate_subfolder": "parents",
            "candidate_tags": ["dad-alcohol"],
            "severity": 0.85,
            "confidence": 0.9,
            "quotes": [{"message_id": msg_ids[1], "text": "папа опять напился вчера"}],
        },
        {
            "summary": "Ритуал общения с Кайросом каждый день в 20:00",
            "candidate_folder": "routines",
            "candidate_subfolder": "rituals",
            "candidate_tags": ["daily-checkin", "8pm"],
            "severity": 0.2,
            "confidence": 0.95,
            "quotes": [{"message_id": msg_ids[2], "text": "я общаюсь с тобой каждый день в 20:00"}],
        },
    ], ensure_ascii=False)


async def test_first_run_creates_three_facts(db_with_messages):
    """Первый прогон: создаются 3 факта, чекпойнт сдвигается."""
    user_id = db_with_messages["user_id"]
    msg_ids = db_with_messages["msg_ids"]

    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm(_extract_response_for_three_messages(msg_ids))),
    ):
        async with async_session_factory() as db:
            agent = ReflectionAgent(db=db)
            result = await agent.run_for_user(user_id)

    assert result.facts_created == 3
    assert result.facts_updated == 0

    async with async_session_factory() as db:
        from sqlalchemy import select
        facts = (await db.execute(
            select(DossierFact).where(DossierFact.user_id == user_id)
        )).scalars().all()
        assert len(facts) == 3
        # Проверим папки
        folders = {(f.folder, f.subfolder) for f in facts}
        assert ("family", "siblings") in folders
        assert ("family", "parents") in folders
        assert ("routines", "rituals") in folders

        # Чекпойнт должен указывать на последнее сообщение
        cp = await db.get(DossierCheckpoint, user_id)
        assert cp is not None
        assert cp.last_processed_message_id == msg_ids[-1]
        assert cp.facts_extracted_total == 3


async def test_second_run_with_no_new_messages_does_nothing(db_with_messages):
    """Второй прогон: если новых сообщений нет — ноль действий."""
    user_id = db_with_messages["user_id"]
    msg_ids = db_with_messages["msg_ids"]

    # Первый прогон
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm(_extract_response_for_three_messages(msg_ids))),
    ):
        async with async_session_factory() as db:
            await ReflectionAgent(db=db).run_for_user(user_id)

    # Второй прогон без новых сообщений
    async with async_session_factory() as db:
        agent = ReflectionAgent(db=db)
        result = await agent.run_for_user(user_id)

    assert result.facts_created == 0
    assert result.facts_updated == 0
    assert result.skipped_reason == "no_new_messages"
```

- [ ] **Шаг 2: Запустить — упадут**

```
cd backend && pytest tests/perception/test_reflection_agent.py -v
```

- [ ] **Шаг 3: Реализовать `backend/app/core/perception/reflection_agent.py`**

```python
"""ReflectionAgent — фоновый агент извлечения фактов из разговоров.

Дизайн: §7 в spec.

Полный цикл (run_for_user):
1. Прочитать чекпойнт пользователя.
2. Загрузить все сообщения пользователя ПОСЛЕ checkpoint_message_id.
3. Если ничего нового — выйти.
4. Extract: один LLM-вызов → массив фактов-кандидатов.
5. Classify+Dedupe: для каждого кандидата — найти существующие факты
   в той же папке, решить (merge / create_new / supersede).
6. Update: применить решения через DossierService.
7. Сдвинуть чекпойнт.

Не зависит от Celery — Celery просто оборачивает run_for_user в таск.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.llm.base import Message as LLMMessage
from app.core.llm.factory import get_provider
from app.core.perception.dossier import DossierService
from app.core.perception.dossier_summary import facts_to_compact_summary
from app.core.perception.folders import is_valid_subfolder
from app.core.perception.reflection_prompt import (
    EXTRACT_SYSTEM_PROMPT,
    DEDUPE_SYSTEM_PROMPT,
    build_extract_user_prompt,
    build_dedupe_user_prompt,
)
from app.data.dossier_models import DossierFact
from app.data.models import ChatSession, Message

logger = logging.getLogger(__name__)


@dataclass
class ReflectionResult:
    """Итог одного запуска агента."""

    facts_created: int = 0
    facts_updated: int = 0
    facts_superseded: int = 0
    candidates_total: int = 0
    candidates_skipped: int = 0  # отброшены из-за невалидной папки
    skipped_reason: str | None = None
    last_processed_message_id: str | None = None


class ReflectionAgent:
    """Агент извлечения фактов. Stateless, создаётся per-call."""

    def __init__(self, *, db: AsyncSession):
        self._db = db
        self._dossier = DossierService(db)

    async def run_for_user(self, user_id: str) -> ReflectionResult:
        """Прогнать полный цикл для одного пользователя."""
        result = ReflectionResult()

        # === Шаг 1: чекпойнт ===
        cp = await self._dossier.get_checkpoint(user_id)
        last_processed_id = cp.last_processed_message_id if cp else None

        # === Шаг 2: загрузить новые сообщения ===
        new_messages = await self._load_new_messages(user_id, last_processed_id)
        if not new_messages:
            result.skipped_reason = "no_new_messages"
            return result

        # === Шаг 3: краткое существующее досье для контекста ===
        existing = await self._dossier.get_facts_by_folders(user_id)
        existing_summary = facts_to_compact_summary(existing)

        # === Шаг 4: Extract ===
        candidates = await self._extract(new_messages, existing_summary)
        result.candidates_total = len(candidates)

        if not candidates:
            # Сдвигаем чекпойнт даже если фактов нет (чтобы не пересматривать)
            await self._dossier.update_checkpoint(
                user_id=user_id,
                last_processed_message_id=new_messages[-1].id,
                facts_extracted=0,
            )
            result.last_processed_message_id = new_messages[-1].id
            return result

        # === Шаг 5+6: Dedupe + Update ===
        for cand in candidates:
            # Валидация папки/подпапки
            folder = cand.get("candidate_folder")
            subfolder = cand.get("candidate_subfolder")
            if not is_valid_subfolder(folder, subfolder):
                logger.warning(
                    "Skipping candidate with invalid folder %s/%s: %r",
                    folder, subfolder, cand.get("summary"),
                )
                result.candidates_skipped += 1
                continue

            decision = await self._dedupe(user_id, cand)

            if decision["decision"] == "merge" and decision.get("target_fact_id"):
                # Добавляем цитаты к существующему факту
                quotes = cand.get("quotes", [])
                # Предполагаем session_id из первой цитаты:
                # все цитаты кандидата — из текущего набора сообщений
                # (можно найти session_id по message_id)
                session_lookup = {m.id: m.session_id for m in new_messages}
                for q in quotes:
                    sid = session_lookup.get(q["message_id"])
                    if sid is None:
                        continue
                    await self._dossier.update_fact_with_new_quote(
                        fact_id=decision["target_fact_id"],
                        new_quote={
                            "text": q["text"],
                            "session_id": sid,
                            "message_id": q["message_id"],
                        },
                        new_severity=cand.get("severity"),
                    )
                result.facts_updated += 1

            elif decision["decision"] in ("create_new", "supersede"):
                # Создаём новый факт
                quotes_input = []
                session_lookup = {m.id: m.session_id for m in new_messages}
                for q in cand.get("quotes", []):
                    sid = session_lookup.get(q["message_id"])
                    if sid is None:
                        continue
                    quotes_input.append({
                        "text": q["text"],
                        "session_id": sid,
                        "message_id": q["message_id"],
                    })

                new_fact = await self._dossier.add_fact(
                    user_id=user_id,
                    folder=folder,
                    subfolder=subfolder,
                    summary=cand["summary"],
                    tags=cand.get("candidate_tags", []),
                    severity=cand.get("severity", 0.5),
                    confidence=cand.get("confidence", 0.5),
                    quotes=quotes_input,
                )
                result.facts_created += 1

                if decision["decision"] == "supersede" and decision.get("target_fact_id"):
                    await self._dossier.supersede_fact(
                        old_fact_id=decision["target_fact_id"],
                        new_fact_id=new_fact.id,
                    )
                    result.facts_superseded += 1

        # === Шаг 7: сдвинуть чекпойнт ===
        await self._dossier.update_checkpoint(
            user_id=user_id,
            last_processed_message_id=new_messages[-1].id,
            facts_extracted=result.facts_created + result.facts_updated,
        )
        result.last_processed_message_id = new_messages[-1].id

        logger.info(
            "Reflection done: user=%s created=%d updated=%d superseded=%d",
            user_id[:8],
            result.facts_created, result.facts_updated, result.facts_superseded,
        )
        return result

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------

    async def _load_new_messages(
        self, user_id: str, after_message_id: str | None,
    ) -> list[Message]:
        """Загрузить сообщения пользователя после чекпойнта (по всем сессиям).

        Если after_message_id None — берём все user-сообщения.
        """
        # Пограничное условие: найти server_timestamp у after_message_id
        cutoff_ts = None
        if after_message_id:
            cutoff_msg = await self._db.get(Message, after_message_id)
            if cutoff_msg:
                cutoff_ts = cutoff_msg.server_timestamp

        # Все сессии этого user_id
        sessions_result = await self._db.execute(
            select(ChatSession.id).where(ChatSession.user_id == user_id)
        )
        session_ids = [row[0] for row in sessions_result]
        if not session_ids:
            return []

        # Сообщения user-роли в этих сессиях, после cutoff_ts
        stmt = (
            select(Message)
            .where(Message.session_id.in_(session_ids))
            .where(Message.role == "user")
            .order_by(Message.server_timestamp.asc())
        )
        if cutoff_ts is not None:
            stmt = stmt.where(Message.server_timestamp > cutoff_ts)

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def _extract(
        self, new_messages: list[Message], existing_summary: str,
    ) -> list[dict]:
        """Вызвать LLM extract-этапа, распарсить JSON-массив."""
        block_lines = []
        for m in new_messages:
            block_lines.append(f"[message_id={m.id}] {m.content}")
        block = "\n".join(block_lines)

        user_prompt = build_extract_user_prompt(
            messages_block=block,
            existing_dossier_summary=existing_summary,
        )

        provider = get_provider()
        response = await provider.generate(
            [
                LLMMessage(role="system", content=EXTRACT_SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=0.2,
            max_tokens=2000,
        )

        # Снять markdown-обёртку если есть
        from app.core.perception.analyzer import strip_markdown_fence
        raw = strip_markdown_fence(response.text)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning("Reflection extract returned non-JSON: %s", e)
            return []

        if not isinstance(data, list):
            logger.warning("Reflection extract returned non-list: %r", type(data))
            return []

        return data

    async def _dedupe(self, user_id: str, candidate: dict) -> dict:
        """Решить, что делать с кандидатом: merge / create_new / supersede.

        Если в той же папке/подпапке нет фактов — сразу create_new (пропуск LLM).
        """
        folder = candidate["candidate_folder"]
        subfolder = candidate.get("candidate_subfolder")

        # Существующие факты в этой папке
        existing = await self._dossier.get_facts_by_folders(
            user_id, folders=[folder],
        )
        # Фильтр по подпапке (если задана)
        if subfolder:
            existing = [f for f in existing if f.subfolder == subfolder]

        if not existing:
            return {"decision": "create_new", "target_fact_id": None}

        # LLM-вызов для решения
        existing_dicts = [
            {"id": f.id, "summary": f.summary, "severity": f.severity}
            for f in existing[:10]  # не больше 10 в контекст
        ]
        candidate_quotes = [q["text"] for q in candidate.get("quotes", [])]

        user_prompt = build_dedupe_user_prompt(
            candidate_summary=candidate["summary"],
            candidate_quotes=candidate_quotes,
            existing_facts=existing_dicts,
        )

        provider = get_provider()
        response = await provider.generate(
            [
                LLMMessage(role="system", content=DEDUPE_SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=0.1,
            max_tokens=300,
        )

        from app.core.perception.analyzer import strip_markdown_fence
        raw = strip_markdown_fence(response.text)

        try:
            decision = json.loads(raw)
            if decision.get("decision") not in ("merge", "create_new", "supersede"):
                logger.warning("Bad dedupe decision: %r", decision)
                return {"decision": "create_new", "target_fact_id": None}
            return decision
        except json.JSONDecodeError:
            return {"decision": "create_new", "target_fact_id": None}
```

- [ ] **Шаг 4: Запустить тесты — пройдут**

```
cd backend && pytest tests/perception/test_reflection_agent.py -v
```

Ожидаемый результат: `2 passed`.

- [ ] **Шаг 5: Коммит**

```
git add backend/app/core/perception/reflection_agent.py backend/tests/perception/test_reflection_agent.py
git commit -m "feat(perception): ReflectionAgent with extract/dedupe/update cycle"
```

---

### Задача 5.4: Celery-таск для запуска агента

**Файлы:**
- Create: `backend/app/core/perception/reflection_tasks.py`
- Modify: `backend/app/api/chat.py` (планировать таск через 15 мин)

- [ ] **Шаг 1: Создать `backend/app/core/perception/reflection_tasks.py`**

```python
"""Celery-таск для запуска ReflectionAgent.

Запускается отложенно через 15 минут после последнего сообщения
пользователя (см. settings.reflection_delay_seconds).

Дедупликация: используем Redis-ключ reflection:scheduled:{user_id} с TTL.
Если новое сообщение приходит до того как таск выстрелил — таск
уже не нужен, потому что новый запланирует себя заново.

Реализация дедупликации: при срабатывании таска проверяем, есть ли
ключ в Redis с тем же `scheduled_at` timestamp. Если timestamp более
свежий — значит был новый запрос, наш таск устарел, выходим.
"""

from __future__ import annotations

import asyncio
import logging

from app.celery_app import celery_app
from app.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.core.perception.reflection_tasks.run_reflection",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def run_reflection(self, user_id: str, scheduled_at: str) -> dict:
    """Celery-обёртка над ReflectionAgent.run_for_user.

    Args:
        user_id: id пользователя.
        scheduled_at: ISO timestamp когда был запланирован запуск.
                      Используется для дедупликации.

    Returns:
        Словарь с метриками для celery result backend.
    """
    return asyncio.run(_run_async(user_id, scheduled_at))


async def _run_async(user_id: str, scheduled_at: str) -> dict:
    """Async-обёртка для вызова из синхронного celery-таска."""
    from app.core.perception.redis_client import get_redis
    from app.core.perception.reflection_agent import ReflectionAgent
    from app.data.database import async_session_factory

    redis = get_redis()
    key = f"reflection:scheduled:{user_id}"

    # Дедупликация: проверяем, что наш scheduled_at — самый свежий запрос
    current = await redis.get(key)
    if current is not None:
        current_str = current.decode() if isinstance(current, bytes) else current
        if current_str != scheduled_at:
            logger.info(
                "Reflection skipped (stale): user=%s ours=%s current=%s",
                user_id[:8], scheduled_at, current_str,
            )
            return {"skipped": "stale_schedule"}

    # Запускаем
    async with async_session_factory() as db:
        agent = ReflectionAgent(db=db)
        result = await agent.run_for_user(user_id)

    # Снимаем флаг (он уже отработал)
    await redis.delete(key)

    return {
        "user_id": user_id,
        "facts_created": result.facts_created,
        "facts_updated": result.facts_updated,
        "facts_superseded": result.facts_superseded,
        "candidates_total": result.candidates_total,
        "skipped_reason": result.skipped_reason,
    }


async def schedule_reflection(user_id: str) -> None:
    """Запланировать (или перепланировать) reflection для пользователя.

    Вызывается из chat.py после каждого сообщения.

    Логика:
    - Записываем в Redis новый scheduled_at timestamp.
    - Запускаем Celery-таск с countdown=15min.
    - Когда таск выстрелит — он проверит, что timestamp в Redis совпадает
      с тем, с которым он был запущен. Если нет — значит был новый запрос,
      наш таск устарел.
    """
    from datetime import datetime, timezone
    from app.core.perception.redis_client import get_redis

    if not user_id:
        # Гость — рефлексию не делаем (нет user_id для досье)
        return

    redis = get_redis()
    key = f"reflection:scheduled:{user_id}"
    scheduled_at = datetime.now(timezone.utc).isoformat()

    await redis.set(key, scheduled_at, ex=settings.reflection_delay_seconds * 2)

    run_reflection.apply_async(
        args=[user_id, scheduled_at],
        countdown=settings.reflection_delay_seconds,
        queue="reflection",
    )
    logger.info(
        "Reflection scheduled: user=%s in %ds",
        user_id[:8], settings.reflection_delay_seconds,
    )
```

- [ ] **Шаг 2: Подключить `schedule_reflection` в `chat.py`**

В `backend/app/api/chat.py` найди блок «=== 9. Обновить счётчик сообщений сессии ===» и `await db.commit()`. ПОСЛЕ commit'а добавь:

```python
    # === 10. Запланировать reflection через 15 минут (только если включён слой) ===
    if settings.use_perception_layer and session.user_id:
        try:
            from app.core.perception.reflection_tasks import schedule_reflection
            await schedule_reflection(session.user_id)
        except Exception:
            logger.exception("Failed to schedule reflection (non-fatal)")
```

- [ ] **Шаг 3: Запустить Celery worker и протестировать вживую**

В одном терминале:
```
cd backend
celery -A celery_worker:celery_app worker -l info -Q reflection -c 1
```

В другом — uvicorn с `USE_PERCEPTION_LAYER=true`:
```
cd backend && USE_PERCEPTION_LAYER=true uvicorn app.main:app --reload --port 8001
```

Создай тестового пользователя, отправь несколько сообщений через `/api/chat` (с `user_id` в БД). В логах uvicorn должно быть:
```
Reflection scheduled: user=... in 900s
```

Для теста уменьши `REFLECTION_DELAY_SECONDS=10` в `.env` и перезапусти.
Через 10 секунд после последнего сообщения в логах Celery worker должно появиться:
```
Reflection done: user=... created=N updated=...
```

И в БД таблица `dossier_facts` должна наполниться.

- [ ] **Шаг 4: Вернуть `REFLECTION_DELAY_SECONDS=900` в `.env`**

- [ ] **Шаг 5: Коммит**

```
git add backend/app/core/perception/reflection_tasks.py backend/app/api/chat.py
git commit -m "feat(perception): celery task and scheduling for ReflectionAgent"
```

---

### Checkpoint Фазы 5

- [ ] `pytest tests/perception/test_reflection_agent.py -v` — зелёное.
- [ ] Celery worker запускается без ошибок (`celery -A celery_worker:celery_app worker`).
- [ ] При включённом флаге `USE_PERCEPTION_LAYER=true` после серии сообщений (с уменьшенным `REFLECTION_DELAY_SECONDS=10` для теста) в БД появляются записи в `dossier_facts`.
- [ ] При новом сообщении до истечения таймера — таск перезапланируется (старый отработает, увидит stale schedule, выйдет).

---

## Фаза 6: UI досье, переключение флага, удаление старого кода

**Цель:**
1. Минимальный UI: пользователь видит свои факты и может удалить любой / всё досье целиком (ФЗ-152 «право на удаление»).
2. Включить флаг `use_perception_layer=true` навсегда.
3. Удалить `crisis/detector.py`, `crisis/keywords.py`, `branch_selector.py` и связанные тесты.
4. Обновить PROGRESS.md.

### Задача 6.1: API endpoints для просмотра/удаления досье

**Файлы:**
- Create: `backend/app/api/dossier.py`
- Modify: `backend/app/api/router.py` (зарегистрировать роутер)
- Test: `backend/tests/test_dossier_api.py`

- [ ] **Шаг 1: Написать тест `backend/tests/test_dossier_api.py`**

```python
"""Тесты API досье."""

from __future__ import annotations

import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_dossier_api.db"
os.environ["LLM_API_KEY"] = "test-key"

from app.data.database import (
    create_all_tables, drop_all_tables, async_session_factory,
)
from app.data.models import User
from app.core.perception.dossier import DossierService


@pytest_asyncio.fixture
async def client_with_user():
    await drop_all_tables()
    await create_all_tables()
    user_id = str(uuid4())
    async with async_session_factory() as db:
        db.add(User(id=user_id, email="t@e.com"))
        await db.commit()

        # Создадим один факт
        service = DossierService(db)
        await service.add_fact(
            user_id=user_id,
            folder="family", subfolder="parents",
            summary="Папа пьёт",
            tags=["dad-alcohol"],
            severity=0.8, confidence=0.9,
            quotes=[],
        )

    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, user_id
    await drop_all_tables()


async def test_list_dossier_returns_facts(client_with_user):
    client, user_id = client_with_user
    # Авторизация-заглушка: на этапе MVP user_id передаётся через query.
    # После Блока 13 (auth) переключим на JWT.
    resp = await client.get(f"/api/dossier?user_id={user_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["facts"]) == 1
    assert data["facts"][0]["summary"] == "Папа пьёт"


async def test_delete_one_fact(client_with_user):
    client, user_id = client_with_user
    list_resp = await client.get(f"/api/dossier?user_id={user_id}")
    fact_id = list_resp.json()["facts"][0]["id"]

    del_resp = await client.delete(
        f"/api/dossier/{fact_id}?user_id={user_id}",
    )
    assert del_resp.status_code == 200

    list_resp_after = await client.get(f"/api/dossier?user_id={user_id}")
    assert len(list_resp_after.json()["facts"]) == 0


async def test_delete_all_dossier(client_with_user):
    client, user_id = client_with_user
    del_resp = await client.delete(f"/api/dossier?user_id={user_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_count"] >= 1


async def test_delete_other_user_fact_forbidden(client_with_user):
    """Нельзя удалить факт другого пользователя."""
    client, user_id = client_with_user
    list_resp = await client.get(f"/api/dossier?user_id={user_id}")
    fact_id = list_resp.json()["facts"][0]["id"]

    other_user = str(uuid4())
    del_resp = await client.delete(
        f"/api/dossier/{fact_id}?user_id={other_user}",
    )
    # Ошибка: либо 403, либо 404 (не наш факт)
    assert del_resp.status_code in (403, 404)
```

- [ ] **Шаг 2: Создать `backend/app/api/dossier.py`**

```python
"""GET / DELETE /api/dossier — просмотр и удаление досье пользователя.

ФЗ-152 «право на исправление и удаление».

MVP-авторизация: user_id передаётся через query параметр (заглушка).
После Блока 13 (auth) переключим на JWT через Depends(get_current_user).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.perception.dossier import DossierService
from app.data.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dossier", tags=["dossier"])


# === DTO для отдачи клиенту ===


class QuoteDTO(BaseModel):
    text: str
    created_at: str


class FactDTO(BaseModel):
    id: str
    folder: str
    subfolder: str | None
    summary: str
    tags: list[str]
    severity: float
    confidence: float
    times_mentioned: int
    first_mentioned: str
    last_mentioned: str
    quotes: list[QuoteDTO]


class DossierResponse(BaseModel):
    facts: list[FactDTO]


class DeleteResponse(BaseModel):
    ok: bool
    deleted_count: int = 0


# === Endpoints ===


@router.get("", response_model=DossierResponse)
async def get_dossier(
    user_id: str = Query(..., description="ID пользователя (после Блока 13 — из JWT)"),
    db: AsyncSession = Depends(get_db),
) -> DossierResponse:
    """Вернуть все факты пользователя (включая superseded для прозрачности)."""
    service = DossierService(db)
    facts = await service.all_user_facts(user_id)

    return DossierResponse(
        facts=[
            FactDTO(
                id=f.id,
                folder=f.folder,
                subfolder=f.subfolder,
                summary=f.summary,
                tags=f.tags,
                severity=f.severity,
                confidence=f.confidence,
                times_mentioned=f.times_mentioned,
                first_mentioned=f.first_mentioned.isoformat(),
                last_mentioned=f.last_mentioned.isoformat(),
                quotes=[
                    QuoteDTO(text=q.text, created_at=q.created_at.isoformat())
                    for q in f.quotes
                ],
            )
            for f in facts
        ],
    )


@router.delete("/{fact_id}", response_model=DeleteResponse)
async def delete_fact(
    fact_id: str,
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> DeleteResponse:
    """Удалить один факт пользователя."""
    service = DossierService(db)
    try:
        await service.delete_fact(user_id=user_id, fact_id=fact_id)
        return DeleteResponse(ok=True, deleted_count=1)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("", response_model=DeleteResponse)
async def delete_all_dossier(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> DeleteResponse:
    """Удалить ВСЁ досье пользователя. Сбрасывает чекпойнт."""
    service = DossierService(db)
    count = await service.delete_all_for_user(user_id)
    logger.info("Dossier wiped: user=%s count=%d", user_id[:8], count)
    return DeleteResponse(ok=True, deleted_count=count)
```

- [ ] **Шаг 3: Зарегистрировать роутер в `backend/app/api/router.py`**

Открой `backend/app/api/router.py`, найди блок импортов роутеров и добавь:
```python
from app.api.dossier import router as dossier_router
```
И в `api_router.include_router(...)` добавь:
```python
api_router.include_router(dossier_router)
```

- [ ] **Шаг 4: Запустить тесты — пройдут**

```
cd backend && pytest tests/test_dossier_api.py -v
```

Ожидаемый результат: `4 passed`.

- [ ] **Шаг 5: Коммит**

```
git add backend/app/api/dossier.py backend/app/api/router.py backend/tests/test_dossier_api.py
git commit -m "feat(perception): GET/DELETE /api/dossier endpoints"
```

---

### Задача 6.2: Frontend — страница профиля с досье

**Файлы:**
- Create: `frontend/app/profile/page.tsx`
- Create: `frontend/components/Dossier/DossierView.tsx`
- Create: `frontend/lib/dossierApi.ts`
- Modify: `frontend/lib/types.ts` (добавить типы DossierFact)

- [ ] **Шаг 1: Добавить типы в `frontend/lib/types.ts`**

В конец файла:

```typescript
// ============================================================================
// Досье (Слой восприятия — Сессия 18+)
// ============================================================================

export interface DossierQuote {
  text: string;
  created_at: string;
}

export interface DossierFact {
  id: string;
  folder: string;
  subfolder: string | null;
  summary: string;
  tags: string[];
  severity: number;
  confidence: number;
  times_mentioned: number;
  first_mentioned: string;
  last_mentioned: string;
  quotes: DossierQuote[];
}

export interface DossierResponse {
  facts: DossierFact[];
}

export interface DeleteResponse {
  ok: boolean;
  deleted_count: number;
}
```

- [ ] **Шаг 2: Создать `frontend/lib/dossierApi.ts`**

```typescript
/**
 * API-обёртка для досье пользователя.
 *
 * ВРЕМЕННО: user_id передаётся через query.
 * После Блока 13 (auth) — заменим на JWT cookie (request пробрасывает credentials).
 */

import type { DossierResponse, DeleteResponse } from "./types";
import { ApiClientError } from "./api";

async function jsonRequest<T>(
  url: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(url, {
    ...options,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new ApiClientError(
      data.error ?? {
        type: "unknown",
        status: res.status,
        message: `HTTP ${res.status}`,
      },
    );
  }
  return data as T;
}

export async function fetchDossier(userId: string): Promise<DossierResponse> {
  return jsonRequest(`/api/dossier?user_id=${encodeURIComponent(userId)}`);
}

export async function deleteFact(
  userId: string,
  factId: string,
): Promise<DeleteResponse> {
  return jsonRequest(
    `/api/dossier/${factId}?user_id=${encodeURIComponent(userId)}`,
    { method: "DELETE" },
  );
}

export async function deleteAllDossier(
  userId: string,
): Promise<DeleteResponse> {
  return jsonRequest(`/api/dossier?user_id=${encodeURIComponent(userId)}`, {
    method: "DELETE",
  });
}
```

- [ ] **Шаг 3: Создать `frontend/components/Dossier/DossierView.tsx`**

```typescript
"use client";

import { useEffect, useState } from "react";

import type { DossierFact } from "@/lib/types";
import {
  fetchDossier,
  deleteFact,
  deleteAllDossier,
} from "@/lib/dossierApi";

/**
 * Просмотр и управление досье пользователя.
 *
 * Группирует факты по папкам, показывает summary + цитаты + severity.
 * Каждый факт можно удалить. Внизу — кнопка «удалить всё».
 *
 * MVP: userId — из props (передаётся со страницы профиля).
 * После Блока 13 — userId из JWT/контекста авторизации.
 */
interface DossierViewProps {
  userId: string;
}

export default function DossierView({ userId }: DossierViewProps) {
  const [facts, setFacts] = useState<DossierFact[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isWiping, setIsWiping] = useState(false);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  async function load() {
    try {
      const res = await fetchDossier(userId);
      setFacts(res.facts);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить досье");
    }
  }

  async function handleDeleteFact(factId: string) {
    if (!confirm("Удалить этот факт? Это действие необратимо.")) return;
    try {
      await deleteFact(userId, factId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка удаления");
    }
  }

  async function handleWipeAll() {
    if (
      !confirm(
        "Удалить ВСЁ досье? Кайрос забудет всё, что узнал о тебе. " +
          "Это действие необратимо.",
      )
    )
      return;
    setIsWiping(true);
    try {
      await deleteAllDossier(userId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка удаления");
    } finally {
      setIsWiping(false);
    }
  }

  if (error) {
    return <div className="text-crisis-700 p-4">⚠️ {error}</div>;
  }

  if (facts === null) {
    return <div className="text-warm-600 p-4">Загружаю досье...</div>;
  }

  if (facts.length === 0) {
    return (
      <div className="text-warm-600 p-4">
        Кайрос ещё ничего не запомнил о тебе. Это появится после нескольких
        бесед.
      </div>
    );
  }

  // Группировка по папкам
  const byFolder = facts.reduce<Record<string, DossierFact[]>>((acc, f) => {
    const key = f.subfolder ? `${f.folder}/${f.subfolder}` : f.folder;
    (acc[key] ??= []).push(f);
    return acc;
  }, {});

  return (
    <div className="max-w-3xl mx-auto p-4 space-y-6">
      <header className="border-b border-warm-200 pb-4">
        <h1 className="text-xl font-semibold text-warm-900">Что знает Кайрос</h1>
        <p className="text-sm text-warm-600 mt-1">
          Это всё, что Кайрос запомнил о тебе из ваших разговоров. Ты можешь
          удалить любой факт или всё сразу.
        </p>
      </header>

      {Object.entries(byFolder).map(([folder, folderFacts]) => (
        <section key={folder}>
          <h2 className="text-md font-medium text-warm-800 mb-2">
            {folder}
          </h2>
          <div className="space-y-3">
            {folderFacts.map((f) => (
              <article
                key={f.id}
                className="bg-warm-50 border border-warm-200 rounded-lg p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <p className="text-warm-900">{f.summary}</p>
                    {f.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {f.tags.map((tag) => (
                          <span
                            key={tag}
                            className="text-xs px-2 py-0.5 bg-warm-200 text-warm-800 rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="text-xs text-warm-500 mt-2">
                      severity: {f.severity.toFixed(2)} · упомянуто{" "}
                      {f.times_mentioned} раз
                    </div>
                    {f.quotes.length > 0 && (
                      <details className="mt-2">
                        <summary className="text-xs text-warm-600 cursor-pointer">
                          Цитаты ({f.quotes.length})
                        </summary>
                        <ul className="mt-2 space-y-1 text-sm text-warm-700 italic">
                          {f.quotes.map((q, i) => (
                            <li key={i}>«{q.text}»</li>
                          ))}
                        </ul>
                      </details>
                    )}
                  </div>
                  <button
                    onClick={() => handleDeleteFact(f.id)}
                    className="text-xs text-crisis-700 hover:text-crisis-900 px-2 py-1"
                    aria-label="Удалить этот факт"
                  >
                    Удалить
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      ))}

      <div className="border-t border-warm-200 pt-4">
        <button
          onClick={handleWipeAll}
          disabled={isWiping}
          className="px-4 py-2 bg-crisis-100 hover:bg-crisis-200 text-crisis-900 rounded-lg text-sm font-medium disabled:opacity-50"
        >
          {isWiping ? "Удаляю..." : "Удалить всё досье"}
        </button>
        <p className="text-xs text-warm-500 mt-2">
          После удаления Кайрос забудет всё, что знал о тебе. Это нельзя
          отменить.
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Шаг 4: Создать `frontend/app/profile/page.tsx`**

```typescript
"use client";

import { useEffect, useState } from "react";

import DossierView from "@/components/Dossier/DossierView";
import { useSession } from "@/hooks/useSession";

/**
 * Страница профиля. На MVP — только просмотр досье.
 * После Блока 13 (auth) добавим: данные аккаунта, подписка и т.д.
 */
export default function ProfilePage() {
  const { guestId } = useSession();
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    // На MVP user_id ≈ guest_id (все гости).
    // После Блока 13 — будет настоящий user_id из /api/auth/me.
    setUserId(guestId);
  }, [guestId]);

  if (!userId) {
    return (
      <div className="p-4 text-warm-600">Подожди, загружаю профиль...</div>
    );
  }

  return <DossierView userId={userId} />;
}
```

- [ ] **Шаг 5: Запустить и проверить вживую**

```
cd frontend && npm run dev
```

Открой `http://localhost:3000/profile`. Если досье пустое — увидишь сообщение «Кайрос ещё ничего не запомнил». После сессии разговоров и срабатывания ReflectionAgent — появятся факты.

- [ ] **Шаг 6: Коммит**

```
git add frontend/lib/types.ts frontend/lib/dossierApi.ts \
        frontend/components/Dossier/ frontend/app/profile/
git commit -m "feat(perception): profile page with dossier view and delete actions"
```

---

### Задача 6.3: Включить флаг постоянно и удалить старый код

**Файлы:**
- Modify: `backend/.env` (USE_PERCEPTION_LAYER=true)
- Delete: `backend/app/core/crisis/detector.py`
- Delete: `backend/app/core/crisis/keywords.py`
- Delete: `backend/app/core/branch_selector.py`
- Modify: `backend/app/api/chat.py` (убрать ветку else)
- Delete: `backend/tests/test_crisis.py` (тесты на удалённый код)
- Modify: `backend/app/data/models.py` (убрать `branch` из ChatSession)
- Create: alembic-миграция для удаления `branch`

⚠️ Это деструктивная задача. Делается ПОСЛЕ того как новая ветка проверена в реальных разговорах несколько дней.

- [ ] **Шаг 1: Включить флаг в `.env`**

```
USE_PERCEPTION_LAYER=true
```

Перезапустить uvicorn, проверить что чат работает.

- [ ] **Шаг 2: Запустить полную ручную проверку**

Серия из 10+ сообщений на разные темы:
- Обычные («привет», «как дела»)
- Намёки («они мне сказали кое-что»)
- Кризис («хочу умереть» — должно быть immediate)
- Семейная история («папа опять напился»)
- Ритуал («буду писать тебе каждый день в 20:00»)

Убедись, что:
- ReflectionAgent создаёт факты после 15 минут.
- На странице `/profile` факты видно.
- Кнопки удаления работают.

Если всё ОК — переходим к удалению старого. Если нет — НЕ удаляй, разбирайся сначала.

- [ ] **Шаг 3: Удалить старые файлы**

```
rm backend/app/core/crisis/detector.py
rm backend/app/core/crisis/keywords.py
rm backend/app/core/branch_selector.py
rm backend/tests/test_crisis.py
```

- [ ] **Шаг 4: Удалить старую ветку из `chat.py`**

В `backend/app/api/chat.py` сделай ровно следующее:

1. Убери импорты:
   ```python
   from app.core.branch_selector import select_branch
   from app.core.crisis.detector import assess_crisis_level
   from app.core.prompts.builder import build_system_prompt
   ```

2. Убери в начале функции `chat()`:
   ```python
   crisis_level = assess_crisis_level(request.message)
   branch = select_branch(request.message)
   ```
   (теперь `crisis_level` берётся из `result.report.risk_level` внутри новой ветки, и `branch` больше не нужен совсем).

3. Замени всю секцию «=== 6/7. Промпт + LLM ===» на:
   ```python
       # === 6. PerceptionPipeline (всегда — без флага) ===
       from app.core.perception.pipeline import PerceptionPipeline
       from app.core.perception.redis_client import get_redis

       history_for_pipeline = [
           {"role": h.role, "content": h.content} for h in request.history
       ]

       try:
           pipeline = PerceptionPipeline(db=db, redis_client=get_redis())
           result = await pipeline.process_message(
               user_id=session.user_id,
               session_id=session.id,
               user_message=request.message,
               history=history_for_pipeline,
           )
           reply_text = result.reply
           crisis_level = result.report.risk_level
           metrics = {
               "response_time_ms": result.response_time_ms,
               "prompt_tokens": result.prompt_tokens,
               "completion_tokens": result.completion_tokens,
           }
           user_msg.perception_json = result.report.model_dump_json()

       except Exception as e:
           logger.exception("Perception pipeline failed: %s", e)
           reply_text = (
               "Извини, я сейчас не могу отвечать. "
               "Если это срочно — нажми SOS вверху для номеров помощи."
           )
           metrics = {"llm_error": f"perception_failed: {type(e).__name__}: {e}"}
           crisis_level = "normal"  # без отчёта точно сказать не можем
   ```

4. Удали константы `_FALLBACK_IMMEDIATE` и `_FALLBACK_GENERIC` целиком — они больше не используются.

5. Удали функцию `_call_llm_with_fallback` целиком.

6. В блоке заполнения crisis_contacts (`if crisis_level != "normal":` — там где он по `request.age_group` строит DTO) — этот блок ОСТАВЬ, но перенеси его ПОСЛЕ pipeline-вызова, потому что `crisis_level` теперь известен только после него.

- [ ] **Шаг 5: Убрать поле `branch` из ChatSession**

В `backend/app/data/models.py` найди ChatSession, удали:
```python
    branch: Mapped[str | None] = mapped_column(String(1), nullable=True)
```

В `backend/app/api/schemas.py` (если поле там есть в `ChatResponse`) — тоже удали.

- [ ] **Шаг 6: Сгенерировать миграцию**

```
cd backend
alembic revision --autogenerate -m "remove branch column from chat_sessions"
alembic upgrade head
```

Проверить, что миграция содержит `op.drop_column('chat_sessions', 'branch')`.

- [ ] **Шаг 7: Удалить настройку `use_perception_layer`**

Поскольку флаг больше не нужен — удалить из `app/config.py` и из `.env.example` (но в `.env` оставить на всякий случай).

В `chat.py` убрать `if settings.use_perception_layer:` обёртку.

- [ ] **Шаг 8: Прогнать все тесты**

```
cd backend && pytest -v
```

Если что-то падает (особенно `test_chat.py`, который раньше тестировал `branch`) — пофиксить.

- [ ] **Шаг 9: Коммит**

```
git add -A
git commit -m "refactor(perception): remove rule-based detector, branch selector, and flag"
```

---

### Задача 6.4: Обновить PROGRESS.md и CLAUDE.md

**Файлы:**
- Modify: `PROGRESS.md`
- Modify: `CLAUDE.md`

- [ ] **Шаг 1: В `PROGRESS.md` обновить блоки 4 и 12**

Блок 4 (Кризисная детекция):
- Старый rule-based удалён.
- Заменён слоем восприятия (см. Сессию 18+).

Блок 12 (NLP):
- Aniemore переносится во Фазу 6+ (после Блока 39).
- Слой восприятия покрывает большую часть того, что планировалось от Блока 12.

- [ ] **Шаг 2: Добавить новый раздел в PROGRESS.md**

После раздела «ИНФРАСТРУКТУРА РЕПО» добавить:

```markdown
## СЛОЙ ВОСПРИЯТИЯ (Сессия 18+)

> **Дизайн**: `docs/superpowers/specs/2026-05-02-perception-layer-design.md`
> **План**: `docs/superpowers/plans/2026-05-02-perception-layer-plan.md`

### ✅ Блок P1 — Dossier (модели данных)
### ✅ Блок P2 — MessageAnalyzer
### ✅ Блок P3 — Mood (Redis)
### ✅ Блок P4 — PerceptionPipeline + интеграция в /api/chat
### ✅ Блок P5 — ReflectionAgent (Celery)
### ✅ Блок P6 — UI досье + удаление старого rule-based
```

- [ ] **Шаг 3: В `CLAUDE.md` обновить раздел «Архитектура приложения»**

Добавить упоминание Redis + Celery в стеке. Обновить упоминание `crisis/detector.py` — он удалён.

- [ ] **Шаг 4: Коммит**

```
git add PROGRESS.md CLAUDE.md
git commit -m "docs(perception): update PROGRESS and CLAUDE for perception layer"
```

---

### Финальный checkpoint

- [ ] `pytest backend/ -v` — всё зелёное.
- [ ] `npm run dev` запускает фронт без ошибок, `/profile` отображает досье.
- [ ] Старые файлы удалены, миграция применена.
- [ ] PROGRESS.md и CLAUDE.md обновлены.
- [ ] Все коммиты на месте.
- [ ] Кайрос отвечает «по-новому» на тестовых сообщениях из спеки (намёки, кризис, контекст).

🎉 Слой восприятия живой.






