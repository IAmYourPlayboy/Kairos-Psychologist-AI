# Устойчивость PerceptionReport к нестабильности LLM-аналайзера: дизайн

> **Версия**: 1.0
> **Дата**: 2026-05-06 (Сессия 20)
> **Статус**: дизайн утверждён пользователем, ждёт review перед передачей в writing-plans
> **Дополняет**: `docs/superpowers/specs/2026-05-02-perception-layer-design.md` (Сессия 18)

---

## 1. Зачем

В Сессии 19 пользователь во время manual regression обнаружил два связанных бага восприятия:

**Баг A — пограничные легитимные вводы валят pipeline**

Пользователь написал «ввв» (бессмысленный ввод). MessageAnalyzer LLM корректно вернул валидный JSON — но с пустыми `dominant_emotion: ""` и `theme: ""`, потому что **у строки «ввв» действительно нет эмоции и темы**. Pydantic-схема `PerceptionReport` имеет `min_length=1` на этих полях → ValidationError → AnalyzerError → fallback с `crisis_level: "normal"`. Пользователь видит ошибку `"perception_failed: AnalyzerError: ..."` в чате.

Это **архитектурная ошибка**: схема слишком строга для естественного «не знаю» от LLM. На любом подобном вводе («аа», «оооо», смайлы, опечатки) pipeline будет срываться.

**Баг B — критический сбой LLM на immediate-триггере**

Пользователь первый раз написал «хочу умереть». LLM-аналайзер вернул не-JSON (предположительно — текст или markdown-объяснение). JSONDecodeError → AnalyzerError → fallback с `crisis_level: "normal"`. **CrisisPanel НЕ открылся автоматически.** Пользователь увидел общий fallback-ответ.

Второй раз с тем же вводом аналайзер отработал нормально → CrisisPanel открылась как положено. То есть это **флакающее поведение** YandexGPT Lite на сложных триггерах.

**По дизайну Сессии 18** (§9 spec): «Если LLM упал — честное "извини, не могу" + SOS-кнопка остаётся доступна (статичные контакты в `crisis/contacts.py`)». То есть Баг B — не нарушение дизайна, а **сознательное принятое в Сессии 18 положение**: при сбое мы не пытаемся угадывать кризис rule-based grep'ом; пользователь увидит ошибку и сможет нажать SOS сам.

**Цель Сессии 20** — снизить частоту обоих сбоев настолько, насколько возможно, **не возвращая rule-based grep**. То есть:

- Уменьшить ложные ValidationError на легитимных пограничных вводах (Баг A).
- Уменьшить вероятность что LLM вернёт мусор (Баг B) — через более чёткий промпт.
- Сохранить принцип Сессии 18 §9: при критическом сбое — `_PERCEPTION_FALLBACK` ответ + видимая SOS-кнопка, никаких grep-страховок.

## 2. Что мы строим

Минималистичная двухслойная защита аналайзера.

```
                  АНАЛАЙЗЕР (как сейчас)
                       │
           LLM возвращает JSON-ответ
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
  parse JSON                  schema validation
  (без изменений)             ┌──────────────────┐
                              │  PerceptionReport │
                              │  УЖЕ нормализует  │
                              │  пустые поля в    │
                              │  «неизвестно».    │
                              │  Длинные тексты — │
                              │  обрезаются.      │
                              └────────┬─────────┘
                                       │
                                       ▼
                              report валидный
                                       │
                                       ▼
                                  pipeline
```

Архитектурно это:

- **Слой 1 (схема)** — `types.py::PerceptionReport` принимает «грязные» данные от LLM и нормализует их в валидный отчёт. Пустая `dominant_emotion` → `"неизвестно"`. Длинный `inner_monologue` → обрезается до `max_length`. Pydantic больше не падает на легитимных «не знаю».

- **Слой 2 (промпт)** — `analyzer_prompt.py` явно говорит LLM: «если не знаешь dominant_emotion / theme — пиши `неизвестно`. Не оставляй поле пустым. Это ломает парсинг.» Снижаем частоту попадания на Слой 1 за счёт более грамотного LLM-поведения.

- **Слой 0 (`analyzer.py`)** — **не трогаем**. Один LLM-вызов, без retry-loop'ов. Если после Слоев 1+2 всё равно падает (JSONDecodeError или ValidationError на нестроковых данных) — пробрасываем AnalyzerError как сейчас. Pipeline в `chat.py` поймает и вернёт `_PERCEPTION_FALLBACK`.

Что **специально не делается**:

- ❌ Никакого rule-based grep на immediate-триггеры в `chat.py`. Принцип Сессии 18 §9 сохранён.
- ❌ Никакого retry-loop с упрощённым промптом. Один вызов — один результат. (Это решение пользователя; подробности в §6 ADR.)
- ❌ Никаких изменений в `analyzer.py`, `pipeline.py`, `mood.py`, `dossier.py` — задача чисто на типы и промпт.

### Принципы

1. **Сессия 18 свята.** Никаких rule-based grep'ов, никаких safety-net по ключевым словам. SOS-кнопка как пассивная защита — единственная страховка при сбое.
2. **Pydantic должен прощать LLM-неопределённость.** «Не знаю» — это валидный ответ, а не баг. Схема его принимает и нормализует.
3. **Промпт говорит LLM как себя вести при неопределённости.** Лучше «неизвестно», чем пусто.
4. **Минимум изменений.** Одна правка `types.py`, одна правка `analyzer_prompt.py`, тесты. Никакой смежной модификации.

## 3. Изменения в `types.py::PerceptionReport`

### 3.1 Поля, которые нормализуются вместо `min_length=1`

Четыре строковых поля, на которых текущая схема валится:

| Поле | Сейчас | После |
|---|---|---|
| `dominant_emotion` | `min_length=1, max_length=50` | пустое → `"неизвестно"`; длиннее 50 → truncate; min_length снят |
| `theme` | `min_length=1, max_length=100` | пустое → `"неизвестно"`; длиннее 100 → truncate; min_length снят |
| `what_user_needs` | `min_length=1, max_length=300` | пустое → `"неясно"`; длиннее **500** (расширили) → truncate; min_length снят |
| `inner_monologue` | `min_length=1, max_length=1000` | пустое → `"(нет мыслей)"`; длиннее **2000** (расширили) → truncate; min_length снят |

**Реализация через `field_validator(mode="before")`** — нормализация происходит ДО Pydantic-валидации длины, поэтому никаких race conditions.

```python
from pydantic import BaseModel, Field, field_validator

class PerceptionReport(BaseModel):
    # ...

    dominant_emotion: str = Field(..., max_length=50, description="...")
    theme: str = Field(..., max_length=100, description="...")
    what_user_needs: str = Field(..., max_length=500, description="...")
    inner_monologue: str = Field(..., max_length=2000, description="...")

    @field_validator("dominant_emotion", mode="before")
    @classmethod
    def _default_dominant_emotion(cls, v: object) -> str:
        if not v or (isinstance(v, str) and not v.strip()):
            return "неизвестно"
        return str(v)[:50]

    @field_validator("theme", mode="before")
    @classmethod
    def _default_theme(cls, v: object) -> str:
        if not v or (isinstance(v, str) and not v.strip()):
            return "неизвестно"
        return str(v)[:100]

    @field_validator("what_user_needs", mode="before")
    @classmethod
    def _default_what_user_needs(cls, v: object) -> str:
        if not v or (isinstance(v, str) and not v.strip()):
            return "неясно"
        return str(v)[:500]

    @field_validator("inner_monologue", mode="before")
    @classmethod
    def _default_inner_monologue(cls, v: object) -> str:
        if not v or (isinstance(v, str) and not v.strip()):
            return "(нет мыслей)"
        return str(v)[:2000]
```

**Расширения `max_length`:**
- `what_user_needs`: 300 → 500. LLM иногда генерит 320-380 символов на сложных кейсах.
- `inner_monologue`: 1000 → 2000. На пограничных кризисных вводах внутренний монолог LLM выходит за 1000 (видел на длинных сообщениях с историей).

Эти лимиты не критичны для семантики — лучше получить чуть длинный отчёт, чем уронить pipeline.

### 3.2 Что НЕ меняется в `PerceptionReport`

- `risk_level` — валидируется как `Literal["normal", "elevated", "high", "immediate"]`. Если LLM вернёт что-то другое — схема упадёт. Это правильно: risk_level критически важен и не должен молча превращаться в дефолт. **Лучше fallback, чем неверный crisis_level.**
- `secondary_emotions`, `hidden_signals`, `open_questions`, `folder_hints` — списки с `default_factory=list, max_length=N`. Пустой список — валидное значение. Не трогаем.
- `trust_level` — float [0.0, 1.0]. Pydantic уронит если LLM вернёт строку или out-of-range. Это правильно.

## 4. Изменения в `analyzer_prompt.py::ANALYZER_SYSTEM_PROMPT`

Добавляем пункт `7` после существующих 6 правил:

> **7. Если ты не уверен в значении поля — пиши `неизвестно` (для строк) или пустой массив (для списков). НЕ оставляй строковые поля пустыми (`""`). Пустые строки ломают парсинг и приводят к fallback-ответу пользователю.**
>
> Конкретно:
>   - `dominant_emotion`: если в сообщении нет явной эмоции (например, бессмысленный текст «ввв», простое «привет» без контекста) → пиши `"неизвестно"`.
>   - `theme`: если темы нет (greeting, шум, междометия) → пиши `"неизвестно"` или `"general"`.
>   - `what_user_needs`: если непонятно — пиши `"неясно"` или `"уточнить"`.
>   - `inner_monologue`: даже если нечего сказать — напиши хотя бы одну фразу-наблюдение от 1 лица (например, «не понимаю что хочет, надо уточнить»). 1000 символов — это потолок, обычно хватает 1-3 предложения.

Также в JSON-схеме промпта меняем требования к минимальной длине:

OLD:
```
"dominant_emotion": str (одно русское слово),
"theme": str (slash-формат, например "family/dad-violence" или "school_peers/bullying"),
"what_user_needs": str (что нужно сейчас: выслушать/совет/план/тишина, до 300 символов),
"inner_monologue": str (мысли Кайроса от 1 лица, 1-3 предложения, до 1000 символов)
```

NEW:
```
"dominant_emotion": str (одно русское слово или "неизвестно"),
"theme": str (slash-формат "family/parents", или "неизвестно" для бессмысленных вводов),
"what_user_needs": str (что нужно сейчас: выслушать/совет/план/тишина/неясно, до 500 символов),
"inner_monologue": str (мысли Кайроса от 1 лица, 1-3 предложения, до 2000 символов)
```

## 5. Тесты

Новый файл `backend/tests/perception/test_perception_robustness.py` с pytest-кейсами. Каждый кейс — один сценарий, который должен пройти после фикса.

```python
"""Устойчивость PerceptionReport к нестабильности LLM-аналайзера.

Сценарии Сессии 20:
- Пустые строки в dominant_emotion / theme / what_user_needs / inner_monologue
  нормализуются в дефолт, не валят pydantic.
- Длинные строки (LLM иногда выходит за max_length) обрезаются.
- Полностью валидный отчёт остаётся валидным.
- Невалидный risk_level — всё ещё ValidationError (важно для безопасности).
"""

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


def test_full_valid_report_passes():
    """Sanity: валидный полный отчёт по-прежнему валиден."""
    report = PerceptionReport(**_full_report())
    assert report.risk_level == "normal"
    assert report.dominant_emotion == "грусть"
    assert report.theme == "general"


def test_invalid_risk_level_still_raises():
    """risk_level — критическое поле, его невалидность должна валить.

    Это сознательно: лучше fallback, чем некорректная маршрутизация
    кризисной семантики.
    """
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        PerceptionReport(**_full_report(risk_level="invalid"))


def test_invalid_trust_level_still_raises():
    """trust_level out-of-range — ValidationError."""
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        PerceptionReport(**_full_report(trust_level=2.0))
```

11 тест-кейсов. Покрывают: 5 сценариев нормализации пустых, 3 сценария truncation, 1 sanity (валидный отчёт), 2 sanity (критические поля по-прежнему валятся).

## 6. ADR (Architectural Decision Record)

Это решение должно быть зафиксировано как архитектурный выбор, чтобы будущие разработчики (включая AI-ассистентов в следующих сессиях) понимали границы.

### ADR-1: Pydantic нормализует «не знаю» вместо валить ошибку

**Контекст:** YandexGPT Lite на пограничных вводах («ввв», эмодзи без текста, шум) возвращает валидный JSON с пустыми строковыми полями. Pydantic с `min_length=1` падает.

**Решение:** Принимаем что LLM может корректно «не знать» — это валидный ответ. Pydantic нормализует пустое в дефолт (`"неизвестно"`), не падает.

**Альтернатива (отклонена):** Сделать LLM строже через промпт, оставить `min_length=1`. Слабость: промпт не гарантирует поведение, особенно у Lite-моделей. Belt-and-suspenders надёжнее.

### ADR-2: Никакого rule-based safety-net в `chat.py`

**Контекст:** Сценарий — LLM-аналайзер упал, в сообщении пользователя есть immediate-триггер («хочу умереть»). Сейчас pipeline возвращает `crisis_level: "normal"` → CrisisPanel не открывается автоматически.

**Решение:** Принцип Сессии 18 §9 сохранён: при критическом сбое — fallback-ответ + видимая SOS-кнопка. Никакого grep по ключевым словам в `chat.py`.

**Альтернатива (отклонена):** мини-список immediate-триггеров (~10 фраз) в `core/crisis/safety_net.py`, который при `AnalyzerError` поднимает `crisis_level` до `immediate`. Принципиально отвергнуто пользователем: «Сессия 18 свята». Аргумент пользователя: SOS-кнопка визуально видна и доступна, пользователь сам нажмёт.

**Что это значит на практике:** известный остаточный риск. Если LLM упадёт на первой попытке immediate-триггера, пользователь получит общий ответ + видимый SOS-кнопку. Пользователь должен либо нажать SOS, либо повторить ввод (со второго раза LLM обычно отрабатывает). Снижение этого риска — задача более стабильного LLM (миграция на Qwen3-14B, см. PROGRESS.md Блок 2.5).

### ADR-3: Никакого retry в analyzer.py

**Контекст:** При сбое аналайзера можно сделать retry с упрощённым промптом — высокая вероятность восстановления.

**Решение:** Без retry. Один вызов — один результат.

**Альтернатива (отклонена):** retry с упрощённым промптом. Стоимость: +0.5₽ на проблемное сообщение, +1-2 секунды latency. Принципиально отвергнуто пользователем — latency в кризисной ситуации хуже честного fallback.

**Альтернативная стратегия снижения частоты сбоев:** улучшение промпта (Слой 2 этого спека) и схемы (Слой 1). Мы делаем upstream-устойчивость, не downstream-recovery.

## 7. Что НЕ делается в этом спеке

- ❌ Изменения в `analyzer.py` (retry-loop)
- ❌ Изменения в `chat.py` (safety-net grep)
- ❌ Изменения в `pipeline.py`, `mood.py`, `dossier.py`
- ❌ Изменения во фронтенде (фронт корректно отображает `chat.error` — это не баг)
- ❌ Миграция LLM на Qwen3-14B — это PROGRESS.md Блок 2.5, отдельный поток работ
- ❌ Расширение `crisis_situations.py` — он остаётся справочником, не используется в pipeline-логике

## 8. Тестирование и acceptance criteria

**Автоматические тесты** (всё в `tests/perception/test_perception_robustness.py`):
- 11 unit-тестов на `PerceptionReport`
- Все должны быть зелёными после фикса

**Manual smoke (после merge)**:
- Перезапустить backend
- Написать в чате «ввв» → не должно быть ошибки `perception_failed` в баннере. Чат должен ответить нормальным текстом.
- Написать «хочу умереть» → CrisisPanel должна открыться **в большинстве случаев** с первого раза (не 100%, потому что LLM флакает; ADR-2 это объясняет).

**Регрессия Сессии 19** (manual):
- Нормальный чат продолжает работать
- Кризисные сценарии (`elevated`/`high`/`immediate`) при успешном анализаторе — без изменений
- Frontend не получает новых типов ответов от backend

## 9. Риски и митигации

| Риск | Митигация |
|---|---|
| LLM научится возвращать `"неизвестно"` слишком часто (laziness) | В промпте явно: «если есть хотя бы намёк — пиши конкретно». Мониторим в логах процент `unknown` через 1-2 недели после деплоя |
| Truncation длинного `inner_monologue` обрежет важную информацию | `inner_monologue` — для отладки. Truncation не влияет на пользователя |
| ADR-2 (отсутствие safety-net) приведёт к реальной проблеме на immediate-триггере | Митигация существует: SOS-кнопка видима. Дополнительная митигация — миграция на более стабильный LLM. Долгосрочно — fine-tune на собственных данных (Data Flywheel) |
| Расширение `max_length` приведёт к раздуванию БД (perception_json) | `inner_monologue` пишется в БД для data flywheel. 2000 chars × 1M сообщений = 2GB. Допустимо |

## 10. Готовность к реализации

После одобрения этого дизайна — переход в writing-plans skill для пошагового плана.

Phases:
- Phase 1: Изменить `types.py::PerceptionReport`
- Phase 2: Изменить `analyzer_prompt.py::ANALYZER_SYSTEM_PROMPT`
- Phase 3: Создать `tests/perception/test_perception_robustness.py`
- Phase 4: Запуск тестов, фикс если что
- Phase 5: Документация (CLAUDE.md, PROGRESS.md — Сессия 20)

---

*Этот документ — спека дополнения к слою восприятия.*

*История правок:*

- *Сессия 20 (2026-05-06): создание после manual regression Сессии 19. Зафиксированы 3 ADR: schema нормализация, отсутствие grep safety-net, отсутствие retry.*
