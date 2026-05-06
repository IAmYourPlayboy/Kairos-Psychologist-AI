# PerceptionReport Robustness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Сделать `PerceptionReport` устойчивым к нестабильности LLM-аналайзера: пустые поля нормализуются в дефолт, длинные обрезаются, промпт явно требует «неизвестно» вместо пустых строк.

**Architecture:** Двухслойная защита без изменения analyzer/pipeline-логики. Слой 1 — `field_validator(mode='before')` в Pydantic-схеме. Слой 2 — явная инструкция в системном промпте аналайзера. Никаких retry, никакого rule-based grep (Сессия 18 §9 свята).

**Tech Stack:** Python 3.11+, Pydantic v2, pytest.

**Spec:** `docs/superpowers/specs/2026-05-06-perception-robustness-design.md`

**Working directory:** `d:/Kairos/.claude/worktrees/perception-safety-net/`. Все пути в плане относительны этой директории, если не указано иначе.

---

## Файлы, которые меняются

| Файл | Действие | Что |
|---|---|---|
| `backend/app/core/perception/types.py` | MODIFY | Снять `min_length=1` с 4 полей `PerceptionReport`, расширить `max_length` для 2 полей, добавить 4 `field_validator(mode='before')` для нормализации пустых и обрезки длинных |
| `backend/app/core/perception/analyzer_prompt.py` | MODIFY | Добавить пункт 7 в `ANALYZER_SYSTEM_PROMPT`, обновить JSON-схему в промпте |
| `backend/tests/perception/test_perception_robustness.py` | CREATE | 11 unit-тестов |
| `CLAUDE.md` | MODIFY | Добавить запись Сессии 20 в «История ключевых решений» |
| `PROGRESS.md` | MODIFY | Добавить запись Сессии 20 |

---

## Phase 1: PerceptionReport schema нормализация

Цель: после этой фазы pydantic не падает на пустых строковых полях, длинные обрезаются. Тесты проходят.

### Task 1.1: Написать failing-тесты для нормализации пустых полей

**Files:**
- Create: `backend/tests/perception/test_perception_robustness.py`

- [ ] **Step 1: Создать файл с тестами**

```python
"""Устойчивость PerceptionReport к нестабильности LLM-аналайзера.

Сценарии Сессии 20:
- Пустые строки в dominant_emotion / theme / what_user_needs / inner_monologue
  нормализуются в дефолт, не валят pydantic.
- Длинные строки (LLM иногда выходит за max_length) обрезаются.
- Полностью валидный отчёт остаётся валидным.
- Невалидный risk_level — всё ещё ValidationError (важно для безопасности).

Спека: docs/superpowers/specs/2026-05-06-perception-robustness-design.md
"""

import pytest
from pydantic import ValidationError

from app.core.perception.types import PerceptionReport


def _full_report(**overrides) -> dict:
    """Дефолт для полного валидного отчёта."""
    return {
        "risk_level": "normal",
        "dominant_emotion": "грусть",
        "secondary_emotions": ["растерянность"],
        "theme": "general",
        "hidden_signals": [],
        "open_questions": [],
        "what_user_needs": "выслушать",
        "trust_level": 0.6,
        "folder_hints": [],
        "inner_monologue": "пользователь делится переживанием, надо мягко присутствовать",
    } | overrides


# ============================================================================
# Нормализация пустых строк
# ============================================================================


def test_empty_dominant_emotion_normalizes_to_unknown():
    report = PerceptionReport(**_full_report(dominant_emotion=""))
    assert report.dominant_emotion == "неизвестно"


def test_whitespace_only_dominant_emotion_normalizes():
    report = PerceptionReport(**_full_report(dominant_emotion="   "))
    assert report.dominant_emotion == "неизвестно"


def test_empty_theme_normalizes_to_unknown():
    report = PerceptionReport(**_full_report(theme=""))
    assert report.theme == "неизвестно"


def test_empty_what_user_needs_normalizes():
    report = PerceptionReport(**_full_report(what_user_needs=""))
    assert report.what_user_needs == "неясно"


def test_empty_inner_monologue_normalizes():
    report = PerceptionReport(**_full_report(inner_monologue=""))
    assert report.inner_monologue == "(нет мыслей)"


# ============================================================================
# Truncation длинных строк
# ============================================================================


def test_long_inner_monologue_truncates():
    long = "Пользователь чувствует тревогу. " * 100  # ~3300 chars
    report = PerceptionReport(**_full_report(inner_monologue=long))
    assert len(report.inner_monologue) <= 2000


def test_long_what_user_needs_truncates():
    long = "Нужно выслушать и поддержать. " * 50  # ~1500 chars
    report = PerceptionReport(**_full_report(what_user_needs=long))
    assert len(report.what_user_needs) <= 500


def test_long_dominant_emotion_truncates():
    report = PerceptionReport(**_full_report(dominant_emotion="а" * 100))
    assert len(report.dominant_emotion) <= 50


# ============================================================================
# Sanity: валидное и критическое
# ============================================================================


def test_full_valid_report_passes():
    """Sanity: валидный полный отчёт по-прежнему валиден."""
    report = PerceptionReport(**_full_report())
    assert report.risk_level == "normal"
    assert report.dominant_emotion == "грусть"
    assert report.theme == "general"


def test_invalid_risk_level_still_raises():
    """risk_level — критическое поле, его невалидность должна валить.

    Это сознательно (см. ADR-1 в spec): лучше fallback, чем некорректная
    маршрутизация кризисной семантики.
    """
    with pytest.raises(ValidationError):
        PerceptionReport(**_full_report(risk_level="invalid"))


def test_invalid_trust_level_still_raises():
    """trust_level out-of-range — ValidationError."""
    with pytest.raises(ValidationError):
        PerceptionReport(**_full_report(trust_level=2.0))
```

- [ ] **Step 2: Проверить что директория `backend/tests/perception/` существует**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net
ls backend/tests/perception/ | head -5
```

Expected: `__init__.py` и существующие perception-тесты. Если директории нет — создать через `mkdir -p` (но она уже должна быть из Сессии 18).

- [ ] **Step 3: Запустить тесты — должны провалиться**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net/backend
pytest tests/perception/test_perception_robustness.py -v
```

Expected: 5 тестов на нормализацию пустых ВАЛЯТСЯ с `ValidationError: String should have at least 1 character`. Тесты truncation тоже валятся (т.к. поля имеют `max_length` который пока не truncate'ит, а валит). Sanity-тесты проходят.

Это нормально — мы пишем failing тесты сначала (TDD).

- [ ] **Step 4: Commit failing тестов**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net
git add backend/tests/perception/test_perception_robustness.py
git commit -m "test(perception): add robustness tests for PerceptionReport (failing)"
```

---

### Task 1.2: Реализовать нормализацию в PerceptionReport

**Files:**
- Modify: `backend/app/core/perception/types.py`

- [ ] **Step 1: Прочитать текущий `types.py`**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net
cat backend/app/core/perception/types.py
```

Поймать структуру: `PerceptionReport` — Pydantic BaseModel с 10 полями. 4 строковых поля имеют `min_length=1`. Импорт `from pydantic import BaseModel, Field` есть.

- [ ] **Step 2: Заменить импорт Pydantic**

В `backend/app/core/perception/types.py` найти строку:

```python
from pydantic import BaseModel, Field
```

Заменить на:

```python
from pydantic import BaseModel, Field, field_validator
```

- [ ] **Step 3: Изменить 4 поля и добавить 4 валидатора**

Найти определение `class PerceptionReport(BaseModel):`. В нём 4 поля сейчас:

```python
    dominant_emotion: str = Field(
        ..., min_length=1, max_length=50,
        description="Главная эмоция (русское слово)",
    )
    # ...
    theme: str = Field(
        ..., min_length=1, max_length=100,
        description="Тема сообщения, slash-формат: 'family/dad-violence'",
    )
    # ...
    what_user_needs: str = Field(
        ..., min_length=1, max_length=300,
        description=(
            "Что нужно пользователю прямо сейчас "
            "(выслушать / совет / план / тишина)"
        ),
    )
    # ...
    inner_monologue: str = Field(
        ..., min_length=1, max_length=1000,
        description=(
            "Внутренние мысли Кайроса от первого лица. "
            "Только для админки/отладки. НЕ показывать пользователю."
        ),
    )
```

Заменить ВСЕ ЧЕТЫРЕ поля (убрать `min_length=1`, расширить `max_length` для 2 полей):

```python
    dominant_emotion: str = Field(
        ..., max_length=50,
        description="Главная эмоция (русское слово или 'неизвестно')",
    )
    # ...
    theme: str = Field(
        ..., max_length=100,
        description="Тема сообщения, slash-формат: 'family/dad-violence' или 'неизвестно'",
    )
    # ...
    what_user_needs: str = Field(
        ..., max_length=500,
        description=(
            "Что нужно пользователю прямо сейчас "
            "(выслушать / совет / план / тишина / неясно)"
        ),
    )
    # ...
    inner_monologue: str = Field(
        ..., max_length=2000,
        description=(
            "Внутренние мысли Кайроса от первого лица. "
            "Только для админки/отладки. НЕ показывать пользователю."
        ),
    )
```

Затем ВНУТРИ класса `PerceptionReport`, после всех `Field`-объявлений, ПЕРЕД любыми методами (если они есть), добавить 4 валидатора:

```python
    # ========================================================================
    # Нормализация пустых строк (Сессия 20).
    # LLM может вернуть пустое поле, если для конкретного ввода нет ясного
    # значения (например, «ввв»). Вместо ValidationError нормализуем в дефолт.
    # Также обрезаем длинные строки на случай если LLM вышел за max_length.
    # См. spec: docs/superpowers/specs/2026-05-06-perception-robustness-design.md
    # ========================================================================

    @field_validator("dominant_emotion", mode="before")
    @classmethod
    def _default_dominant_emotion(cls, v: object) -> str:
        if v is None or (isinstance(v, str) and not v.strip()):
            return "неизвестно"
        return str(v)[:50]

    @field_validator("theme", mode="before")
    @classmethod
    def _default_theme(cls, v: object) -> str:
        if v is None or (isinstance(v, str) and not v.strip()):
            return "неизвестно"
        return str(v)[:100]

    @field_validator("what_user_needs", mode="before")
    @classmethod
    def _default_what_user_needs(cls, v: object) -> str:
        if v is None or (isinstance(v, str) and not v.strip()):
            return "неясно"
        return str(v)[:500]

    @field_validator("inner_monologue", mode="before")
    @classmethod
    def _default_inner_monologue(cls, v: object) -> str:
        if v is None or (isinstance(v, str) and not v.strip()):
            return "(нет мыслей)"
        return str(v)[:2000]
```

⚠ Важно: валидаторы обрезают через slicing `str(v)[:N]` — это совместимо с `max_length=N` в Field (slice → длина ≤ N → Pydantic не валит).

⚠ Важно: `@classmethod` декоратор обязателен для `field_validator` в Pydantic v2.

- [ ] **Step 4: Запустить новые тесты**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net/backend
pytest tests/perception/test_perception_robustness.py -v
```

Expected: все 11 тестов PASSED.

- [ ] **Step 5: Запустить ВСЕ тесты perception, чтобы убедиться что не сломали Сессию 18**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net/backend
pytest tests/perception/ -v 2>&1 | tail -25
```

Expected: все perception-тесты проходят (включая существующие `test_chat_perception.py`, `test_dossier_api.py` если они в этой директории, или их аналоги).

Если что-то упало — это значит что мы сломали Сессию 18. **Стоп.** Прочитать ошибку, понять root cause, починить, вернуться к шагу 4.

- [ ] **Step 6: Commit реализации**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net
git add backend/app/core/perception/types.py
git commit -m "feat(perception): normalize empty strings in PerceptionReport (Session 20)"
```

---

## Phase 2: Analyzer prompt — явное «неизвестно»

Цель: после этой фазы LLM получает чёткую инструкцию писать `"неизвестно"` вместо пустых строк. Снижает частоту попадания на Слой 1.

### Task 2.1: Обновить ANALYZER_SYSTEM_PROMPT

**Files:**
- Modify: `backend/app/core/perception/analyzer_prompt.py`

- [ ] **Step 1: Прочитать текущий промпт**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net
cat backend/app/core/perception/analyzer_prompt.py | head -90
```

Поймать структуру: `ANALYZER_SYSTEM_PROMPT` — большая f-string-подобная переменная (но не f-string, обычная многострочная строка). После пункта 6 идёт описание JSON-схемы.

- [ ] **Step 2: Найти и обновить пункт «6. ОТВЕЧАТЬ СТРОГО ВАЛИДНЫМ JSON»**

Найти строку:

```
6. ОТВЕЧАТЬ СТРОГО ВАЛИДНЫМ JSON по схеме (поля и типы):
```

И блок ниже до закрывающей фигурной скобки JSON-схемы:

```
{
  "risk_level": "normal" | "elevated" | "high" | "immediate",
  "dominant_emotion": str (одно русское слово),
  "secondary_emotions": [str, ...] (до 5 русских слов),
  "theme": str (slash-формат, например "family/dad-violence" или "school_peers/bullying"),
  "hidden_signals": [str, ...] (до 5),
  "open_questions": [str, ...] (до 5 — о чём бы стоило спросить),
  "what_user_needs": str (что нужно сейчас: выслушать/совет/план/тишина, до 300 символов),
  "trust_level": float (0.0-1.0 — насколько пользователь сейчас открыт),
  "folder_hints": [str, ...] (формат "folder/subfolder", до 10),
  "inner_monologue": str (мысли Кайроса от 1 лица, 1-3 предложения, до 1000 символов)
}
```

Заменить на:

```
6. ОТВЕЧАТЬ СТРОГО ВАЛИДНЫМ JSON по схеме (поля и типы):

{
  "risk_level": "normal" | "elevated" | "high" | "immediate",
  "dominant_emotion": str (одно русское слово или "неизвестно"),
  "secondary_emotions": [str, ...] (до 5 русских слов),
  "theme": str (slash-формат "family/parents", или "неизвестно" для бессмысленных вводов),
  "hidden_signals": [str, ...] (до 5),
  "open_questions": [str, ...] (до 5 — о чём бы стоило спросить),
  "what_user_needs": str (выслушать/совет/план/тишина/неясно, до 500 символов),
  "trust_level": float (0.0-1.0 — насколько пользователь сейчас открыт),
  "folder_hints": [str, ...] (формат "folder/subfolder", до 10),
  "inner_monologue": str (мысли Кайроса от 1 лица, 1-3 предложения, до 2000 символов)
}

7. ЕСЛИ НЕ УВЕРЕН в значении строкового поля — пиши "неизвестно" / "неясно" / "(нет мыслей)".
   НЕ оставляй строковые поля пустыми (""). Пустые строки исторически ломали парсинг
   и приводили к fallback-ответу пользователю; теперь они нормализуются автоматически,
   но лучше написать содержательный дефолт.

   Конкретно:
   - dominant_emotion: если в сообщении нет явной эмоции (бессмысленный текст «ввв»,
     простое «привет» без контекста) → "неизвестно".
   - theme: если темы нет (greeting, шум, междометия) → "неизвестно" или "general".
   - what_user_needs: если непонятно — "неясно" или "уточнить".
   - inner_monologue: даже если нечего сказать — напиши хотя бы одну фразу-наблюдение
     от 1 лица (например, «не понимаю что хочет, надо уточнить»).
```

⚠ Важно: после строки `Никакого текста вне JSON. Никаких объяснений. Никаких markdown-обёрток.` ничего не меняем — она остаётся в конце.

- [ ] **Step 3: Проверить что промпт всё ещё корректно собирается**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net/backend
python -c "from app.core.perception.analyzer_prompt import ANALYZER_SYSTEM_PROMPT; print('OK, length:', len(ANALYZER_SYSTEM_PROMPT))"
```

Expected: вывод `OK, length: <число>` без exception. Длина обычно 3000-5000 символов с FOLDER_TAXONOMY.

- [ ] **Step 4: Проверить что подстановка `{{FOLDER_TAXONOMY}}` всё ещё работает**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net/backend
python -c "from app.core.perception.analyzer_prompt import ANALYZER_SYSTEM_PROMPT; assert '{{FOLDER_TAXONOMY}}' not in ANALYZER_SYSTEM_PROMPT, 'FOLDER_TAXONOMY не подставился'; assert 'family' in ANALYZER_SYSTEM_PROMPT, 'нет family в taxonomy'; print('OK: taxonomy подставлен')"
```

Expected: `OK: taxonomy подставлен`. Если `assert` упал — мы случайно сломали `.replace()`-логику в конце файла.

- [ ] **Step 5: Запустить весь тестовый набор бэкенда (sanity)**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net/backend
pytest tests/ -v 2>&1 | tail -15
```

Expected: все тесты проходят. Если что-то упало — читать root cause, чинить.

- [ ] **Step 6: Commit**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net
git add backend/app/core/perception/analyzer_prompt.py
git commit -m "feat(perception): instruct LLM to write 'неизвестно' instead of empty strings"
```

---

## Phase 3: Документация

Цель: зафиксировать решение в CLAUDE.md и PROGRESS.md.

### Task 3.1: Обновить CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Найти секцию «История ключевых решений»**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net
grep -n "Сессия 19" CLAUDE.md | head -3
```

Expected: одна строка с записью Сессии 19 (вокруг строки 970-1000).

- [ ] **Step 2: Добавить запись Сессии 20 после Сессии 19**

В CLAUDE.md, в секции «История ключевых решений», ПОСЛЕ последнего пункта Сессии 19 (это будет markdown-list с `**Сессия 19**` заголовком и буллетами), ПЕРЕД маркером `---` или следующей секцией, добавить:

```markdown
**Сессия 20** (Май 2026): 🛡️ **Устойчивость PerceptionReport к нестабильности LLM-аналайзера.** Точечный фикс двух багов из Manual Regression Сессии 19:
- **Баг A** («ввв» / пограничный ввод): LLM возвращал валидный JSON с пустыми `dominant_emotion`/`theme` → Pydantic `min_length=1` валился → `AnalyzerError` → fallback с ошибкой в чате.
- **Баг B** (первое «хочу умереть»): LLM возвращал не-JSON → JSONDecodeError → fallback с `crisis_level: "normal"` → CrisisPanel НЕ открывался автоматически.

**Решение:** двухслойная защита, **БЕЗ rule-based grep и БЕЗ retry**:
- Слой 1 (`types.py`): `field_validator(mode='before')` нормализует пустые `dominant_emotion`/`theme`/`what_user_needs`/`inner_monologue` в дефолтные строки. Длинные обрезаются. `min_length=1` снят.
- Слой 2 (`analyzer_prompt.py`): пункт 7 — явная инструкция LLM «если не знаешь — пиши `неизвестно`».

**3 ADR зафиксированы в спеке:**
- **ADR-1:** Pydantic нормализует «не знаю» вместо валить ошибку.
- **ADR-2:** НЕТ rule-based safety-net в `chat.py`. Принцип Сессии 18 §9 свят. SOS-кнопка как пассивная защита — единственная страховка при сбое. Известный остаточный риск Бага B принят.
- **ADR-3:** НЕТ retry в `analyzer.py`. Один вызов = один результат. Latency в кризисе хуже честного fallback.

**11 unit-тестов** в `tests/perception/test_perception_robustness.py`.

**Не трогали:** `analyzer.py`, `chat.py`, `pipeline.py`, frontend.

Дизайн: `docs/superpowers/specs/2026-05-06-perception-robustness-design.md`
План: `docs/superpowers/plans/2026-05-06-perception-robustness.md`
```

- [ ] **Step 3: Обновить шапку CLAUDE.md (версия + дата)**

В CLAUDE.md, найти строку:

```
> **Версия**: 3.5 | **Дата**: Май 2026 (Сессия 19)
```

Заменить на:

```
> **Версия**: 3.6 | **Дата**: Май 2026 (Сессия 20)
```

- [ ] **Step 4: Commit**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net
git add CLAUDE.md
git commit -m "docs(claude-md): record Session 20 (PerceptionReport robustness)"
```

---

### Task 3.2: Обновить PROGRESS.md

**Files:**
- Modify: `PROGRESS.md`

- [ ] **Step 1: Найти секцию «История правок» в конце файла**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net
tail -25 PROGRESS.md
```

Expected: блок `*История правок:*` с записями 16.1, 16.2, 17.0, 17.1, 18.0, 19.0. Версия 2.6.

- [ ] **Step 2: Добавить запись 20.0 ПОСЛЕ 19.0**

Найти строку:

```
- *19.0: 🎨 **Frontend redesign по черновику Figma Make.** ...
```

ПОСЛЕ неё (на следующей строке) добавить:

```
- *20.0: 🛡️ **Устойчивость PerceptionReport.** Двухслойная защита от нестабильности YandexGPT Lite на пограничных вводах: `field_validator(mode='before')` нормализует пустые `dominant_emotion`/`theme`/`what_user_needs`/`inner_monologue` в дефолты («неизвестно»/«неясно»/«(нет мыслей)»), длинные строки обрезаются. Расширены `max_length`: `inner_monologue` 1000→2000, `what_user_needs` 300→500. ANALYZER_SYSTEM_PROMPT (пункт 7): явная инструкция LLM писать «неизвестно» вместо пустых строк. **БЕЗ retry, БЕЗ rule-based grep** (3 ADR в спеке). 11 unit-тестов. Не трогали `analyzer.py`, `chat.py`, `pipeline.py`, frontend. Дизайн: `docs/superpowers/specs/2026-05-06-perception-robustness-design.md`. План: `docs/superpowers/plans/2026-05-06-perception-robustness.md`.*
```

- [ ] **Step 3: Обновить версию в самом конце файла**

Найти строку:

```
*Версия: 2.6*
```

Заменить на:

```
*Версия: 2.7*
```

И строку:

```
*Последнее обновление: Сессия 19, Май 2026*
```

Заменить на:

```
*Последнее обновление: Сессия 20, Май 2026*
```

- [ ] **Step 4: Commit**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net
git add PROGRESS.md
git commit -m "docs(progress): record Session 20 (PerceptionReport robustness)"
```

---

## Phase 4: Финальная проверка

### Task 4.1: Полный тест-suite + git log

- [ ] **Step 1: Прогон всех тестов**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net/backend
pytest tests/ -v 2>&1 | tail -20
```

Expected: все тесты проходят. Особенно важно:
- 11 новых тестов из `test_perception_robustness.py` — все PASSED
- Существующие perception-тесты не сломаны
- Существующие тесты `chat`, `dossier`, `feedback` не сломаны (если они есть в backend/tests/)

Если что-то упало — стоп, разбираться.

- [ ] **Step 2: Git log для проверки коммитов**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net
git log --oneline main..HEAD
```

Expected: 5 коммитов в правильном порядке:
1. `test(perception): add robustness tests for PerceptionReport (failing)`
2. `feat(perception): normalize empty strings in PerceptionReport (Session 20)`
3. `feat(perception): instruct LLM to write 'неизвестно' instead of empty strings`
4. `docs(claude-md): record Session 20 (PerceptionReport robustness)`
5. `docs(progress): record Session 20 (PerceptionReport robustness)`

(Плюс `aa9cb5b docs(perception): spec for PerceptionReport robustness (Session 20)` — это спека, она уже была закоммичена до начала плана.)

- [ ] **Step 3: Smoke check ANALYZER_SYSTEM_PROMPT**

Финальная проверка что промпт собирается и содержит ключевые слова Сессии 20:

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net/backend
python -c "
from app.core.perception.analyzer_prompt import ANALYZER_SYSTEM_PROMPT
assert 'неизвестно' in ANALYZER_SYSTEM_PROMPT, 'нет инструкции про неизвестно'
assert 'family' in ANALYZER_SYSTEM_PROMPT, 'taxonomy не подставился'
assert 'до 500 символов' in ANALYZER_SYSTEM_PROMPT, 'не обновили what_user_needs limit'
assert 'до 2000 символов' in ANALYZER_SYSTEM_PROMPT, 'не обновили inner_monologue limit'
print('OK: промпт содержит все обновления Сессии 20')
"
```

Expected: `OK: промпт содержит все обновления Сессии 20`. Если упало — какая-то правка не дошла, чинить.

- [ ] **Step 4: Smoke check PerceptionReport нормализации**

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net/backend
python -c "
from app.core.perception.types import PerceptionReport

# 1. Пустые поля нормализуются
r = PerceptionReport(
    risk_level='normal',
    dominant_emotion='',
    theme='',
    what_user_needs='',
    inner_monologue='',
    secondary_emotions=[],
    hidden_signals=[],
    open_questions=[],
    folder_hints=[],
    trust_level=0.5,
)
assert r.dominant_emotion == 'неизвестно'
assert r.theme == 'неизвестно'
assert r.what_user_needs == 'неясно'
assert r.inner_monologue == '(нет мыслей)'
print('OK: нормализация пустых работает')

# 2. Длинные обрезаются
r2 = PerceptionReport(
    risk_level='normal',
    dominant_emotion='а' * 100,
    theme='general',
    what_user_needs='x' * 1000,
    inner_monologue='y' * 5000,
    secondary_emotions=[],
    hidden_signals=[],
    open_questions=[],
    folder_hints=[],
    trust_level=0.5,
)
assert len(r2.dominant_emotion) <= 50
assert len(r2.what_user_needs) <= 500
assert len(r2.inner_monologue) <= 2000
print('OK: truncation работает')
"
```

Expected: оба `OK`. Если что-то упало — это пограничный случай который тесты пропустили, чинить.

- [ ] **Step 5: Финальный commit-сводка (опционально)**

Если всё зелёное — пустой commit-маркер для отметки что фикс готов:

```bash
cd d:/Kairos/.claude/worktrees/perception-safety-net
git commit --allow-empty -m "test(perception): Session 20 robustness verified end-to-end"
```

---

## Готово!

После всех 4 фаз:
- ✅ `PerceptionReport` принимает пустые/длинные строковые поля без ошибок
- ✅ Промпт явно требует «неизвестно» вместо пустых строк
- ✅ 11 unit-тестов проходят
- ✅ Существующие тесты Сессии 18 не сломаны
- ✅ CLAUDE.md и PROGRESS.md документируют Сессию 20

**Manual smoke** (после merge в main):
- В чате написать «ввв» → не должно быть ошибки `perception_failed: AnalyzerError` в баннере. Бот отвечает обычно.
- В чате написать «хочу умереть» → CrisisPanel должна открыться **в большинстве случаев** с первого раза. Не 100% — флакает LLM, ADR-2 это объясняет. SOS-кнопка как fallback всегда видна.

**Если что-то на одном из шагов не сработает** — стоп, разобраться, не двигаться дальше.
