# Design: Code audit — от кустарности к системности

> **Дата**: 2026-05-12 (Сессия 29)
> **Источник запроса**: идея 9 из [`docs/ideas/backlog.md`](../../ideas/backlog.md) + пользователь просит все идеи бэклога в PROGRESS.md, начать с 9-й.
> **Статус**: DRAFT — требует ревью пользователя до перевода в implementation plan.
> **Scope**: `backend/app/` + `frontend/components/` + `frontend/lib/` + `frontend/hooks/` + `frontend/app/` + `scripts/`. **НЕ** включает: `backend/agents/` (до Фазы 2), `backend/tests/` (отдельный audit), `docs/`, `skills/`.

---

## 1. Назначение

Провести систематический разбор кустарности в кодовой базе Кайроса и превратить его в последовательный план рефакторинга. Результат дизайна — **список находок с классификацией по типу проблемы, серьёзности и предложенному плану фикса**. Пользователь на ревью решает: что берём в новую фазу PROGRESS.md, что откладываем, что режем.

**Критерии кустарности** (согласованы с пользователем):
1. Магические строки / числа
2. Дублирование логики
3. Отсутствие схемы валидации там где данные важны
4. if-elif-лестницы где просится таблица правил
5. Разбросанная ответственность без карты
6. Глобальное состояние без чёткой причины
7. Длинные функции / файлы делающие несколько вещей
8. Неявные контракты между слоями
9. Отсутствие публичного API у модуля
10. Копипаст вместо наследования/композиции

---

## 2. Метод

**Уровень A** (систематический скан): grep по маркерам (файлы >500 строк, TODO/FIXME/HACK, bare except, print в live-коде, eval, os.getenv vs config, cross-module импорты), обход всех `__init__.py`, проверка публичных API.

**Уровень B** (ручное чтение): только модули, которые уровень A подсветил как проблемные или архитектурно важные (pipeline, analyzer, prompt_builder, therapy_router, api.ts, error_handler, config).

Оба уровня выполнены. Общий объём прочитанного кода: ~4500 строк напрямую + навигация по остальному через grep. Ничего не меняется в коде в рамках этого дизайна.

---

## 3. Что работает хорошо (эталоны системности)

Важно зафиксировать, потому что остальной код нужно подтягивать **к этому уровню**, а не выдумывать новый.

### 3.1 `backend/app/config.py`

Весь доступ к окружению централизован через Pydantic Settings. `os.getenv` / `os.environ` **не встречается нигде** в `backend/app` (подтверждено grep). `PLACEHOLDER_API_KEYS` — set-константа, не магические строки. Валидаторы на LLM_API_KEY, JWT_SECRET_KEY, DATABASE_URL с понятными сообщениями падения. `model_config` с `env_nested_delimiter="__"`. Эталон — как должен выглядеть любой модуль с «настройками».

### 3.2 `backend/app/middleware/error_handler.py` ↔ `frontend/lib/api.ts::ApiClientError`

Двусторонний контракт с прописанной нормализацией. Backend: если `HTTPException(detail=dict)` — кладёт `message` как строку, весь dict идёт в `details`. Frontend: defensive coercion на случай если контракт нарушится. Оба файла содержат **комментарии-ссылки друг на друга** и объясняют почему нормализация такая какая есть (с примером Сессии 22 про soft-delete). Это редко встречается в кодовой базе и это пример того как должен выглядеть каждый контракт между слоями.

### 3.3 `backend/app/core/perception/pipeline.py`

193 строки, 7 нумерованных шагов с комментариями, единственная функция `process_message`. Stateless класс. Принимает db+redis в конструкторе (нет импорта singletons внутри методов). Единственный `except Exception` — строка 138 для ASQ-override, явно помечен `noqa: BLE001` и логируется как non-fatal. Эталон файла-оркестратора.

### 3.4 `backend/app/core/llm/` (вся директория)

Чистая абстракция: `BaseLLMProvider` (ABC) → `OpenAICompatProvider` → `factory.get_provider()`. `extra_body.py` с `disable_reasoning()` (Сессия 22) — правильно вынесенная магия. `MockLLMProvider` для e2e. Подменить Yandex на Cloud.ru = одна переменная окружения. Эталон абстракции.

### 3.5 `backend/app/core/perception/types.py`

Pydantic-модели с field_validator'ами (нормализация пустых строк из Сессии 20). Одна точка истины для `PerceptionReport` — ни analyzer, ни pipeline, ни prompt_builder своих копий не имеют.

---

## 4. Находки: каталог кустарности

Каждая находка имеет:
- **ID** (для ссылок из PROGRESS.md)
- **Тип** (один из 10 критериев)
- **Серьёзность** (🔴 блокирует развитие / 🟡 болит / 🟢 косметика)
- **Доказательство** (grep-вывод, цифры, цитаты)
- **Что предлагаю**
- **Цена** (грубая оценка: S ≤ 1 день / M ≤ 3 дня / L ≤ 1-2 недели)
- **Зависимости** (блокирует ли что-то из PROGRESS.md)

---

### 4.1 🔴 МЁРТВЫЙ КОД: `therapy_router.py` + `prompts/builder.py` + `user_memory/` + `crisis_situations.py`

**Тип**: #2 (дублирование), #5 (разбросанная ответственность), #10 (копипаст).

**Серьёзность**: 🔴 блокирует Фазу 3.0 (подключение therapy_router в pipeline).

**Доказательства**:

**A. `core/therapy_router.py`** — 445 строк, `TherapyRouter` + `THERAPY_GRAPH` с 12 узлами + `determine_goal` + `choose_technique` + `route`.
- Используется только в: `prompts/builder.py` (сам мёртвый) + `tests/test_therapy_router.py` + `knowledge/THERAPY_ROUTER_ARCHITECTURE.md`.
- В продуктовом потоке (`api/chat.py` → `pipeline.py` → `perception/prompt_builder.py`) **не вызывается ни разу**.
- Содержит `eval(prereq)` на строке 311 (security smell — но не эксплуатируется потому что не вызывается).
- Содержит bare `except:` на строке 313 — единственный bare except в живом коде (по grep).
- Содержит `if __name__ == "__main__"` с `print()` демкой — файл сам себя тестирует вручную.

**B. `core/prompts/builder.py`** — 318 строк. Функция `build_system_prompt(branch, crisis_level, ...)`.
- Тянет `suggest_*_technique` из `knowledge/*.py` и `TherapyRouter` из `therapy_router.py`.
- Используется только в: `tests/test_prompts.py` + `tests/test_therapy_router.py`.
- В продуктовом потоке используется `perception/prompt_builder.py::build_main_prompt` — совершенно другой сборщик. То есть тесты «на промпты» — тестируют мёртвый билдер, а не тот что реально идёт в Qwen.

**C. `core/user_memory/`** — 5 файлов (dossier.py, extractor.py, compressor.py, storage.py, updater.py), суммарно ~830 строк.
- Старая версия досье до Сессии 18 (класс `UserDossier` на Pydantic, файловое хранилище).
- Используется только своими же файлами (grep `from app.core.user_memory` — всё внутри папки).
- Живая версия: `core/perception/dossier.py` (DossierService + DB).

**D. `core/knowledge/crisis_situations.py`** — **4449 строк** (четверть всего backend!).
- 300+ `CrisisSituation` dataclass'ов с keywords.
- Grep по всему проекту: **0 импортов** (кроме собственного `if __name__ == "__main__"`).
- Docstring говорит «Используется в: app/core/therapy_router.py» — но router его не импортирует.

**E. `knowledge/*.py::suggest_*_technique` функции** — `suggest_pfa_technique`, `suggest_sfbt_technique`, `suggest_dbt_skill`, `suggest_act_process`.
- Импортируются только в: `therapy_router.py` (мёртв) + `prompts/builder.py` (мёртв).
- В живом `perception/prompt_builder.py::_pick_technique_digest` используется совершенно другой путь: digest-строки из `knowledge/digests.py` через `if-elif` по маркерам.

**Что предлагаю** (один атомарный шаг):

1. **Удалить `core/therapy_router.py`** целиком.
2. **Удалить `core/prompts/builder.py`** + связанные тесты `tests/test_prompts.py`, `tests/test_therapy_router.py`.
3. **Удалить `core/user_memory/`** директорию целиком + `tests/test_user_memory*` если есть.
4. **Удалить `core/knowledge/crisis_situations.py`** + `core/knowledge/THERAPY_ROUTER_ARCHITECTURE.md`.
5. **Удалить `suggest_*_technique` функции** из `who_pfa.py`, `sfbt_mi.py`, `dbt_skills.py`, `act_processes.py`, `cbt_techniques.py` (включая `get_distortion_by_keywords`, `ALL_DBT_SKILLS`, `ACT_PROCESSES` если после удаления suggest — они только эти функции и обслуживали).
6. Попутно чистим demo-блоки `if __name__ == "__main__":` с `print()` — они в `cbt_techniques.py`, `act_processes.py`, `who_pfa.py`, `sfbt_mi.py`, `dbt_skills.py`, `crisis_situations.py`, `forbidden_phrases.py` (последний — смотреть отдельно, он живой).
7. **Важно**: перед удалением нужна **явная инвентаризация** идей которые **есть только в мёртвом коде** и нигде больше. Возможные кандидаты:
   - Концепция `TherapyGoal` (6 целей) + `TechniqueCategory` как enum'ы — могут пригодиться в Фазе 3.0 (TherapySession.current_goal).
   - 12 техник в `THERAPY_GRAPH` с prerequisites/next_nodes — как данные могут пригодиться, но структура «граф» избыточна.
   - 300+ ситуаций в `crisis_situations.py` — могут быть нужны как **test fixtures** для обкатки сценариев (Фаза 1.1 `scenarios.md`). Надо проверить совпадение.

   Перед удалением — **сохранить эти концепции в новый short-файл** `docs/ideas/from_dead_code.md`, чтобы не потерять мысли.

**Цена**: S (1 день). Это самая дешёвая победа и самая жирная — убираем ~1750 строк кода (вся `therapy_router.py` + `prompts/builder.py` + `user_memory/` + `suggest_*` функции, **без `crisis_situations.py`** — он идёт отдельно, см. 4.1.5). Плюс сам `crisis_situations.py` 4449 строк перерабатывается в данные для регрессии (см. 4.1.5).

**Зависимости**:
- **Разблокирует** Фазу 3.0 (при ревизии therapy_router теперь очевидно — удалить, заменить на TherapySession + расширенный `_pick_technique_digest`).
- **Разблокирует** Фазу 3.7.3 (digests для Child Mode) — не надо решать, трогать ли мёртвые `suggest_*`.
- **Ничего не ломает** в pytest (389 passed → ожидается 389 - N где N = тесты над мёртвым кодом, скорее всего 20-30). Нужно перепроверить каждый удаляемый тест: правда ли он тестирует мёртвое, или по ошибке тестирует живое.

---

### 4.1.5 🔴 `crisis_situations.py` (4449 строк) — переработка, не снос

**Тип**: данные, не код. Решение отдельное от 4.1.

**Серьёзность**: 🔴 — 4449 строк данных без единого импорта, но данные **имеют ценность** которую нельзя потерять.

**Доказательства**: `backend/app/core/knowledge/crisis_situations.py` — 300+ экземпляров `CrisisSituation(id, category, title, description, severity, recommended_approach, keywords)`. Категории: утрата, травма, отношения, здоровье, карьера, семья, финансы, зависимости, + специфичные группы (медработники, учителя, военные, полиция/спасатели, мигранты, мобилизация, контрактники, эмиграция из-за войны, политические репрессии). **0 импортов по всему проекту.**

Это не научные эталонные статьи (у них нет `consensus`, `nuances`, `sources`, `confidence` — см. формат `knowledge_base/psychology/grief/ca_grief_20260427.md`). Это **гипотетические сценарии с ключевыми словами**, созданные вручную.

**Что предлагаю (вариант 2 из обсуждения с пользователем)**:

1. Создать `scripts/convert_crisis_to_scenarios.py` — разовая конвертация:
   - Проходит по `CRISIS_SITUATIONS` dict
   - Генерирует `docs/playtests/scenarios_generated.md` в формате `scenarios.md`
   - Маппинг: `severity` → `risk_level` (critical→immediate, high→high, medium→elevated, low→normal), `recommended_approach` → ожидаемая ветка (PFA→B, SIX_CS→A, по умолчанию по первому элементу списка), `keywords` → стартовая фраза сценария
   - `description` идёт как «контекст сценария»
   - Возрастная группа — дефолт `adult` (Child-специфичные сценарии будут в 3.7.6 отдельно)

2. Пользователь просматривает `scenarios_generated.md`, выбирает **~50-70 полезных** для беты (обогащают текущий scenarios.md с 30 до ~80-100). Остальные ~220-250 — в архив.

3. Архив: экспорт всех `CrisisSituation` в `data/archive/crisis_situations_archive.yaml`. YAML-формат, без Python-кода. Хранится в репозитории как потенциальный источник тем для PubMed-агентов Фазы 2 (список тем для исследования) или для Child Mode adaptation (какие сюжеты специфичны для детей).

4. После этого `backend/app/core/knowledge/crisis_situations.py` сносится. Оригинал сохраняется в git-истории.

**Цена**: M (1-1.5 дня — скрипт + ревью сгенерированных сценариев пользователем + экспорт в YAML).

**Зависимости**:
- Независимо от 4.1 (но логически идёт рядом с ним в одной фазе).
- **Расширяет Фазу 1.1** (список сценариев обкатки).
- **Питает Фазу 2** как стартовый список тем PubMed-агентов.

**Открытая тема (пользователь зафиксировал на Сессии 29)**: как именно ложить научные эталонные статьи в `knowledge_base/psychology/` — обсудим отдельно при подходе к Фазе 2. Сейчас для `crisis_situations.py` эталонный формат **не применяется** — это сценарии, не статьи.

---

### 4.2 🔴 KNOWLEDGE/ — разные схемы данных, нет базовой модели

**Тип**: #3 (нет валидации), #10 (копипаст структур).

**Серьёзность**: 🔴 блокирует Фазу 3.7.3 (каждый digest должен содержать `forbidden_phrases_in_context` — а у текущих файлов нет даже базового поля) и Фазу 2 (PubMed-агенты будут плодить новые файлы knowledge/ — без схемы каждый будет чуть другой).

**Доказательства**:

Каждый файл в `core/knowledge/` определяет **свой отдельный dataclass** без общей базы:
- `six_cs.py::SixCComponent` (name, russian_name, description, goal, techniques, example_questions, when_to_use, contraindications)
- `cbt_techniques.py::CognitiveDistortion` (name, description, examples, reframe_technique, reframe_example)
- `dbt_skills.py::DBTSkill` (name, module, description, when_to_use, steps, example)
- `who_pfa.py`, `act_processes.py`, `sfbt_mi.py`, `nlp_markers.py`, `crisis_situations.py::CrisisSituation` — каждый со своим полем-набором.
- `digests.py` — строки-константы с фиксированным неформальным форматом «## ПОДХОД / ШАГИ / ЧЕГО НЕ ДЕЛАТЬ».

Принцип CLAUDE.md «двухуровневая система запретов» (Сессия 27) требует поля `forbidden_phrases_in_context` — но **ни в одной модели его нет как поля**. Запреты прописаны внутри строк digest'ов свободным текстом, не извлекаются программно.

PubMed-агенты в ADR из Фазы 3.7.7 требуют: «Каждая эталонная статья содержит поле `forbidden_phrases_in_context`». Без общей схемы агенты будут генерировать файлы в формате "на глаз посмотрели на соседние".

**Принятое решение (Сессия 29)**: вариант Б — **единая Pydantic-модель `TechniqueDigest`**, не расширение существующих dataclass'ов.

**Обоснование через масштаб 1000 пользователей/день**:

При 1000 пользователей × 5-10 сообщений = 5000-10000 сообщений/день × 2 LLM-вызова = ≈100-200 LLM-вызовов/минуту в пике. Каждый вызов подбирает digest.

- **По производительности** варианты А и Б **одинаковы** — техники загружаются один раз при импорте приложения, живут в памяти, доступ O(1). Валидация Pydantic при старте добавляет ~100мс на ~50 техник, пренебрежимо.
- **По разработке** вариант Б выигрывает кратно: PubMed-агенты Фазы 2 и 3.7.7 добавят **десятки новых техник**. Без единой схемы каждая новая будет чуть в своём формате — через полгода 12 разных моделей. С единой схемой — один шаблон для агента и Pydantic ловит ошибки при старте приложения, а не в рантайме.
- **По расширению** `forbidden_phrases_in_context` обязателен для Child Mode 3.7.3. В варианте А его надо добавить к 6 разным dataclass'ам руками. В варианте Б — одно поле в одной модели.

**Что предлагаю**:

1. Создать новый модуль `core/knowledge/schema.py` с Pydantic-моделями:
   ```python
   class ForbiddenPhrase(BaseModel):
       phrase: str
       alternative: str | None
       reason: str  # почему нельзя в этом контексте

   class TechniqueDigest(BaseModel):
       id: str                    # machine-readable ID, используется в правилах выбора
       name: str                  # человеко-читаемое
       approach_label: str        # "ВОЗ PFA — ЗАЗЕМЛЕНИЕ", "SIX C's" — для заголовка в промпте
       when_applies: str          # описание ситуации для роутера (не для промпта)
       body_for_prompt: str       # готовый текст блока, идёт в LLM
       forbidden_phrases_in_context: list[ForbiddenPhrase]  # обязательное поле
       source: str                # ссылка на scientific paper / эталонную статью
       trust_level: Literal["core", "validated", "experimental"]
       age_groups: list[str]      # ["adult"], ["child", "adult"], ...
   ```
2. Переписать текущие `digests.py` как набор `TechniqueDigest`-экземпляров (сохранив содержимое строк как `body_for_prompt`). Добавить `forbidden_phrases_in_context` реально извлечёнными из «ЧЕГО НЕ ДЕЛАТЬ» блоков.
3. `core/knowledge/digests.py` превращается в **каталог**: `ALL_DIGESTS: dict[str, TechniqueDigest]`.
4. `_pick_technique_digest` переписать чтобы возвращать `TechniqueDigest`, а не голую строку. В `build_main_prompt` — форматировать блок из `digest.approach_label + digest.body_for_prompt`, отдельно инжектить `forbidden_phrases_in_context` как негативы.
5. Если `core/knowledge/six_cs.py`, `cbt_techniques.py`, `dbt_skills.py`, `act_processes.py`, `who_pfa.py`, `sfbt_mi.py`, `nlp_markers.py` после очистки 4.1 **ничем больше не используются** — снести их. Они были источниками для `suggest_*` которые мы удаляем. **Проверить grep'ом после 4.1.**

**Цена**: M (2-3 дня).

**Зависимости**:
- **После 4.1** (мёртвый код убран и мы понимаем что реально остаётся).
- **Разблокирует Child Mode 3.7.3** (digest-схема готова к `forbidden_phrases_in_context`).
- **Разблокирует PubMed-агентов Фазы 2.7** (ModuleBuilderAgent знает в какую схему писать).

---

### 4.3 🟡 `_pick_technique_digest` — if-elif на 8 правилах

**Тип**: #4 (if-elif где просится таблица).

**Серьёзность**: 🟡 работает, но растёт плохо.

**Доказательства**: `perception/prompt_builder.py:80-134`. 8 правил через последовательные `if return`. Каждое правило — комбинация условий на `risk_level`, `dominant_emotion`, `theme` с `_matches_any(text, markers)`. Маркеры — кортежи строк: `_GRIEF_MARKERS`, `_ANXIETY_MARKERS`, `_SIX_CS_MARKERS`, и т.д.

Когда появится Child Mode, придётся добавить 8 новых правил (child_grief, child_bullying, child_abuse, etc.) — итого 16 веток в одной функции. Когда PubMed-агенты сгенерируют новые техники — ещё N.

**Что предлагаю** (после 4.2, когда есть `TechniqueDigest`):

В `TechniqueDigest` добавить поле `selection_rule: SelectionRule` где SelectionRule — Pydantic-модель:

```python
class SelectionRule(BaseModel):
    risk_levels: list[Literal["normal", "elevated", "high", "immediate"]]
    emotion_markers: list[str] = []   # any-match
    theme_markers: list[str] = []     # any-match
    age_groups: list[str] = ["adult"]
    priority: int                     # при совпадении нескольких — выигрывает с большим priority
    exclude_if: list[str] = []        # рег.условия исключения (для immediate — None)
```

`_pick_technique_digest` становится:
```python
def pick_digest(report, age_group) -> TechniqueDigest | None:
    candidates = [d for d in ALL_DIGESTS.values() if _matches(d.selection_rule, report, age_group)]
    if not candidates: return None
    return max(candidates, key=lambda d: d.selection_rule.priority)
```

8 правил → 8 `TechniqueDigest`-экземпляров с `selection_rule`. Новое правило = новый экземпляр, не правка функции.

**Цена**: S (0.5 дня после 4.2).

**Зависимости**: после 4.2.

---

### 4.4 🟡 Промпты — нет карты «что инжектится в какой LLM-вызов»

**Тип**: #5 (разбросанная ответственность без карты), #8 (неявные контракты).

**Серьёзность**: 🟡 разработчик не видит целиком что уходит в Qwen. Плюс мешает аудиту промпта глазами (который нужен в Фазе 1 обкатки).

**Доказательства**: промпты идут в LLM из 4 разных мест, каждое собирает свой prompt:

| LLM-вызов | Сборщик | Компоненты |
|---|---|---|
| Analyzer | `perception/analyzer_prompt.py::ANALYZER_SYSTEM_PROMPT + build_analyzer_user_prompt` | Системный промпт + `WHO_PFA_DISTRESS_LEVELS` digest + история + досье + текущее сообщение |
| Main reply | `perception/prompt_builder.py::build_main_prompt` | `prompts/base.py::BASE_PROMPT` + `prompts/crisis.py::build_crisis_prompt` + mood + dossier facts + technique digest + inner_monologue + what_user_needs |
| Reflection extract | `perception/reflection_prompt.py` | Своя сборка + `CBT_TRIGGERS` + `DBT_TRIGGERS` digest |
| Reflection dedupe | тот же файл | Отдельный промпт для классификации+дедупликации |

Плюс мёртвые `prompts/builder.py::build_system_prompt` и мёртвые branch_a/branch_b которые используются только в мёртвом builder.

Есть `prompts/base.py`, `prompts/crisis.py`, `prompts/forbidden_phrases.py`, `prompts/human_style.py`, `prompts/branch_a.py`, `prompts/branch_b.py` — 7 файлов. Без карты разработчик не может ответить «какие из них реально идут в Qwen, а какие для мёртвого билдера».

**Что предлагаю**:

1. Создать **карту** `docs/architecture/prompt-composition.md` (один markdown файл, ~2 экрана) с таблицей:
   - Какой LLM-вызов
   - Какая функция собирает system prompt
   - Какие компоненты входят (с путями к файлам)
   - В каком порядке
   - Примерная длина в токенах

2. После 4.1: выяснить что `branch_a.py`, `branch_b.py` используются только мёртвым builder → удалить если так.

3. Проверить `prompts/human_style.py` и `prompts/forbidden_phrases.py`:
   - `human_style.py` — похоже используется в `base.py` как фрагмент. Проверить.
   - `forbidden_phrases.py` (352 строки + CLI с print) — проверить, используется ли за пределами своего `__main__`. Если нет — это **инструмент разработчика для проверки ответов LLM на запрещённые фразы**, легальный use-case, но его надо либо убрать из `app/` и переместить в `scripts/`, либо чётко задокументировать.

4. Когда будет Фаза 1.5.8 (dev-панель) — trace-режим последнего сообщения там опирается на эту карту.

**Цена**: S (0.5 дня — карта) + S (0.5 дня — снос branch_a/b, переезд forbidden_phrases в scripts).

**Зависимости**: после 4.1.

---

### 4.5 🟡 `auth.py` (620 строк) делает слишком много

**Тип**: #7 (длинный файл, несколько концептов).

**Серьёзность**: 🟡 работает и покрыто тестами (Сессия 22), но дальше расти плохо.

**Доказательства**: `backend/app/api/auth.py` 620 строк. Концепты в одном файле:
- `/register` + миграция guest сессий + консенты
- `/login` с constant-time проверкой
- `/refresh` с rotation + burn-on-replay
- `/logout` (одно устройство) + `/logout-everywhere`
- `/me` (GET профиль) + `DELETE /me` (soft-delete)
- `/me/cancel-deletion`
- `_issue_tokens_and_set_cookies` helper
- `_client_meta`, `_to_user_response` helpers

В Фазе 8.11 (OAuth-методы) сюда придут `/telegram`, `/vk`, `/sms` — файл станет 1000+ строк.

**Что предлагаю**:

Разбить по концептам:
- `api/auth/register.py` (регистрация + миграция guest)
- `api/auth/login.py` (login + refresh + logout)
- `api/auth/account.py` (/me, delete, cancel)
- `api/auth/__init__.py` — собирает router из подроутеров
- `api/auth/_helpers.py` — `_client_meta`, `_to_user_response`, `_issue_tokens_and_set_cookies`

В Фазе 8.11 OAuth-методы пойдут в отдельные `api/auth/telegram.py` / `vk.py` / `sms.py`.

**Цена**: S (0.5 дня). Это структурный сплит, импорты нужно аккуратно обновить, но логика не меняется.

**Зависимости**: нет блокеров. **Разблокирует** Фазу 8.11 (OAuth-методы — без сплита будет мегафайл).

---

### 4.6 🟡 `data/models.py` (515 строк) — вся модель БД в одном файле

**Тип**: #7 (длинный файл, несколько доменов).

**Серьёзность**: 🟡 терпимо, но при появлении TherapySession / UserState / ToolInvocation / TwinProfile (Фазы 1.5, 3.0, 3.6, 5) файл становится 1500+ строк.

**Доказательства**: `models.py` — User, ChatSession, Message, FeedbackEvent, Subscription, ScreeningResult, UserConsent, RefreshToken (8 таблиц). Плюс отдельный `dossier_models.py` уже отдельно (правильно).

**Что предлагаю**:

Разбить по доменам:
- `data/models/auth.py` — User, RefreshToken, UserConsent
- `data/models/chat.py` — ChatSession, Message, FeedbackEvent
- `data/models/billing.py` — Subscription
- `data/models/screening.py` — ScreeningResult
- `data/models/__init__.py` — реэкспорт всех для обратной совместимости
- `data/dossier_models.py` — уже отдельно, оставить

Старые импорты `from app.data.models import User` работают через `__init__.py`. Alembic миграции не трогаются (SQLAlchemy metadata единая через `Base`).

**Цена**: S (0.5 дня).

**Зависимости**: нет блокеров. **Уменьшает риск** при Фазе 1.5.1 (UserState — новая большая модель со множеством полей).

---

### 4.7 🟢 `HumanTypingEffect.tsx` + `KairosProviders.tsx` — большие frontend файлы

**Тип**: #7 (длинный файл).

**Серьёзность**: 🟢 косметика. Работает хорошо, тесты зелёные.

**Доказательства**:
- `KairosProviders.tsx` — 360 строк, обёртка всех Context Provider'ов. Можно порезать на мелкие файлы (`ThemeProvider`, `SessionProvider`, etc.), но они и так в отдельных хуках. Провайдеры собираются в одном месте — это нормально.
- `HumanTypingEffect.tsx` — 110 строк (в рамках нормы).
- `useChat.ts` — 321 строка, единственный хук чата, содержит логику optimistic updates + error recovery + sync с Dexie. Это комплексный хук, но он в одном месте — а не разбросан. OK.

**Что предлагаю**: **ничего**. Эти файлы крупные, но концептуально целостные. Разбиение ради разбиения только навредит.

Исключение: если при Фазе 1.5.1 (UserState) `useChat.ts` будет расти — вынести логику UserState-чтения в отдельный `useUserState.ts`. Но это задача самой Фазы 1.5, не аудита.

**Цена**: 0.

---

### 4.8 🟢 Демо-скрипты `if __name__ == "__main__"` с print в live-модулях

**Тип**: #7 (файл делает две вещи: быть импортируемым модулем И CLI-демкой).

**Серьёзность**: 🟢 запах, а не проблема.

**Доказательства** (grep `print(` в `backend/app/core`):
- `cbt_techniques.py:255-262` — демка
- `act_processes.py:280-288` — демка
- `who_pfa.py`, `sfbt_mi.py`, `dbt_skills.py` — аналогично
- `forbidden_phrases.py:345-352` — CLI-проверка запрещённых фраз
- `crisis_situations.py:4443-4449` — демка
- `therapy_router.py:438-445` — демка
- `extractor.py:97` — `print(f"Error extracting facts: {e}")` в `user_memory/` (мёртв)

**Что предлагаю**:
- Большая часть уйдёт с 4.1 (мёртвый код).
- То что останется (если `forbidden_phrases.py` жив и нужен как CLI) — переехать в `scripts/validate_forbidden.py`, импортируя из `core/prompts/forbidden_phrases.py`.

**Цена**: S (0.3 дня, после 4.1).

---

### 4.9 🟢 `Dict[str, X]` / `List[X]` / `Optional[X]` вместо современного синтаксиса

**Тип**: #9 (старый стиль).

**Серьёзность**: 🟢 косметика. Python 3.11+ (в pyproject) поддерживает `dict[str, X]`, `list[X]`, `X | None`.

**Доказательства**: `core/therapy_router.py:15` (мёртв, уходит), `core/knowledge/*.py` (частично уходят с 4.1/4.2), `user_memory/dossier.py` (мёртв), кое-где в `auth.py` (живой).

**Что предлагаю**: массовый автомат через `ruff --select UP --fix` в живом коде. Плюс включить правило UP в pre-commit/CI (Фаза 8.4).

**Цена**: S (15 минут на автоматический прогон, 1-2 часа на ревью diff'а).

**Зависимости**: нет.

---

### 4.10 🟢 Магическая строка `"adult"` / `"child"` / `"youth"` без enum

**Тип**: #1 (магические строки).

**Серьёзность**: 🟢 косметика. Но уже встречается в:
- `prompts/crisis.py::build_crisis_prompt(age_group)` (Сессия 27)
- `perception/pipeline.py::process_message(age_group)` (Сессия 27)
- `perception/prompt_builder.py::build_main_prompt(age_group)` (Сессия 27)
- `api/chat.py::ChatRequest.age_group`
- `crisis/contacts.py::get_crisis_contacts(age_group)`
- Frontend: `lib/crisis-contacts.ts::getCrisisContacts(ageGroup)`

Типа `str | None` сейчас, без enum. Child Mode (Фаза 3.7) **удвоит** количество мест где эта строка протекает.

**Что предлагаю**: ввести `app/core/age.py::AgeGroup` как `Literal["child", "youth", "adult"]` **и как реестр констант**:
```python
AGE_GROUP_CHILD = "child"
AGE_GROUP_YOUTH = "youth"
AGE_GROUP_ADULT = "adult"
AgeGroup = Literal["child", "youth", "adult"]
```
Протянуть тип через все сигнатуры. Frontend — `type AgeGroup` в `types.ts` с теми же значениями.

**Цена**: S (0.3 дня).

**Зависимости**: нужно до Фазы 3.7 (Child Mode).

---

### 4.11 🟢 Магические строки `"normal"` / `"elevated"` / `"high"` / `"immediate"`

**Тип**: #1.

**Серьёзность**: 🟢 косметика, но тот же паттерн что 4.10.

**Доказательства**: `risk_level` как `str` везде. `PerceptionReport.risk_level: Literal[...]` уже есть в `types.py` — это хорошо. Но в коде сравнения `if risk == "immediate"` на магических строках.

**Что предлагаю**: `app/core/risk.py::RiskLevel` + константы, как в 4.10. Или расширить `types.py` добавив `class RiskLevel(StrEnum)`. Протянуть.

**Цена**: S (0.3 дня).

**Зависимости**: нет.

---

### 4.12 🟢 TODO-комментарии без тикета

**Тип**: недопрограммированные хвосты.

**Доказательства** (2 штуки):
- `api/auth.py:463-464` (по контексту account_deletion): `# === Subscription: TODO (Блок F) ===`
- `api/sessions.py:243`: `# TODO: добавить ChatSession.title (миграция) и сохранять.`

**Что предлагаю**: привязать к PROGRESS.md — первый к Фазе 8 (ЮKassa), второй к Фазе 1.5 (UserState либо в той же миграции добавить title). Заменить TODO-комменты на ссылки: `# См. PROGRESS.md Фаза 1.5.X`.

**Цена**: 15 минут.

---

## 5. Что НЕ нашлось (отсутствие плохих паттернов)

Отдельно фиксирую, чтобы не забыть.

- **`os.getenv` / `os.environ` в приложении**: 0 вхождений (всё через `config.Settings`). ✅
- **`eval` / `exec` в живом коде**: 0 (только в мёртвом `therapy_router.py:311`). ✅
- **bare `except:` в живом коде**: 0 (только в мёртвом `therapy_router.py:313`). Все живые `except Exception` с `noqa` и логированием. ✅
- **Синглтоны-через-глобальные-переменные**: только `redis_client` и `provider` в `factory.get_provider()` — оба оправданы и тестируемы (MockLLMProvider подменяется флагом e2e_mode). ✅
- **FIXME / HACK / XXX**: 0 в `backend/app/core` и `frontend/`. ✅
- **Неявный контракт между backend и frontend**: задокументирован в `error_handler.py` ↔ `api.ts`. ✅
- **Отсутствие type hints**: в большинстве живого кода hints есть. ✅
- **Plural/singular inconsistency в именах таблиц**: все в plural (`users`, `messages`, `chat_sessions`). ✅

---

## 6. Сводная таблица находок

| ID | Тип | 🔥 | Название | Цена | Блокирует | Подразумевает |
|---|---|---|---|---|---|---|
| 4.1 | dead code | 🔴 | Снос `therapy_router` + `prompts/builder` + `user_memory/` + `suggest_*` | S | Фаза 3.0 | ~1750 строк код-delete |
| 4.1.5 | данные | 🔴 | `crisis_situations.py` (4449) → тестовые сценарии + YAML-архив | M | обогащает Фазу 1.1, Фазу 2 | разовая конвертация |
| 4.2 | schema | 🔴 | `TechniqueDigest` как Pydantic-модель + `forbidden_phrases_in_context` | M | Child Mode 3.7.3, PubMed 2.7 | зависит от 4.1 |
| 4.3 | if-elif | 🟡 | `SelectionRule` внутри digest'а вместо 8 веток | S | — | зависит от 4.2 |
| 4.4 | карта | 🟡 | `docs/architecture/prompt-composition.md` + чистка branch_a/b | S | dev-панель 1.5.8 | зависит от 4.1 |
| 4.5 | сплит | 🟡 | `auth.py` → `api/auth/{register,login,account,_helpers}.py` | S | Фаза 8.11 (OAuth) | — |
| 4.6 | сплит | 🟡 | `models.py` → `data/models/{auth,chat,billing,screening}.py` | S | Фаза 1.5.1 (UserState) | — |
| 4.7 | — | 🟢 | Frontend большие файлы — **ничего не делаем** | 0 | — | — |
| 4.8 | chore | 🟢 | Демки `__main__` с print → переезд или удаление | S | — | зависит от 4.1 |
| 4.9 | chore | 🟢 | `Dict[]`/`List[]`/`Optional[]` → современный синтаксис | S | — | `ruff --select UP --fix` |
| 4.10 | magic | 🟢 | `AgeGroup` enum + константы | S | Child Mode 3.7 | — |
| 4.11 | magic | 🟢 | `RiskLevel` enum + константы | S | — | — |
| 4.12 | chore | 🟢 | 2 TODO → ссылки на PROGRESS.md | XS | — | — |

**Итого**: 3 🔴 + 4 🟡 + 6 🟢 = 13 находок. Общая цена: ≈ 7-9 дней работы при последовательном исполнении. Большая часть — низкорисковые удаления и структурные сплиты.

---

## 7. Предлагаемый порядок выполнения

Порядок важен — многие находки зависят друг от друга, попытка сделать параллельно приведёт к merge-аду.

### Шаг 1 (день 1, атомарный): **Инвентаризация перед сносом** (4.1-подготовка)
Перед удалением — сохранить идеи из мёртвого кода в `docs/ideas/from_dead_code.md`:
- `TherapyGoal` 6 целей (потенциально пригодится в Фазе 3.0 как `TherapySession.current_goal`)
- `TechniqueCategory` enum (потенциально — категоризация в `TechniqueDigest`)
- Концепция графа техник с `next_nodes` (как идея многошагового маршрута, не код)

`CrisisSituation` данные — **НЕ теряются** через 4.1.5 (отдельная переработка), здесь не фиксируем.

### Шаг 2 (день 1-2): **4.1 Снос мёртвого кода (без crisis_situations)**
Делаем в одном коммите с явным списком удалённого: `therapy_router.py`, `prompts/builder.py`, `user_memory/`, `suggest_*` функции + enum'ы/dict'ы которые их обслуживали. Прогоняем pytest — ожидаем что упадёт N тестов (над мёртвым кодом), удаляем их. Остальные тесты зелёные.

### Шаг 2.5 (день 2-3): **4.1.5 `crisis_situations.py` → сценарии + архив**
- Пишем `scripts/convert_crisis_to_scenarios.py`, запускаем, получаем `docs/playtests/scenarios_generated.md`.
- Пользователь просматривает, выбирает ~50-70 сценариев в основной `scenarios.md` (обогащают с 30 до ~80-100).
- Экспорт всех 300+ `CrisisSituation` в `data/archive/crisis_situations_archive.yaml`.
- Сносим `backend/app/core/knowledge/crisis_situations.py`.

### Шаг 3 (день 2-4): **4.2 `TechniqueDigest` схема**
Пишем Pydantic-модель. Мигрируем 7 текущих digest-строк в 7 экземпляров. Заполняем `forbidden_phrases_in_context` из существующего «ЧЕГО НЕ ДЕЛАТЬ» текста. `_pick_technique_digest` возвращает модель, `build_main_prompt` форматирует.

### Шаг 4 (день 4): **4.3 `SelectionRule`**
Добавить `selection_rule` в каждый digest. Переписать `_pick_technique_digest` на функцию фильтра+сортировки. 8 правил → 8 `selection_rule` в данных.

### Шаг 5 (день 5): **4.10+4.11 Enums**
`AgeGroup` и `RiskLevel` как типы+константы. Протянуть через все сигнатуры. Это до Фазы 3.7.

### Шаг 6 (день 5-6): **4.5 auth.py сплит** + **4.6 models.py сплит**
Оба структурных сплита идут вместе. После — быстрый прогон pytest для проверки импортов.

### Шаг 7 (день 6): **4.4 Карта промптов** + **4.8 чистка демок** + **4.9 ruff UP** + **4.12 TODO**
Пачка мелочей.

**Итого: 7-8 календарных дней чистой работы** при 100% концентрации. В реальности — 1.5-2.5 недели между обкаткой (Фаза 1).

---

## 8. Риски и что НЕ делаем в этой фазе

### Риски

1. **При удалении мёртвого кода потеряем идею которая окажется нужна**. Митигация: шаг 1 (инвентаризация).
2. **Тесты над мёртвым кодом ≠ 100% мёртвые** — некоторые могут косвенно тестировать живое через import-chain. Митигация: прогон pytest после каждого удаления, читать каждый падающий тест перед тем как его удалять.
3. **`TechniqueDigest` схема + Child Mode в параллель** — два проекта правят `core/knowledge/`. Митигация: 4.2 идёт **до** Фазы 3.7, не параллельно.
4. **Alembic миграция при сплите `models.py`** — SQLAlchemy metadata должен остаться единой через `Base`. Если `Base` импортируется из разных мест — auto-migration генерирует дубликаты. Митигация: `Base` остаётся в одном месте, в `data/models/__init__.py`; подмодули импортируют его оттуда.

### Что явно не делаем в этой фазе

- **Рефакторинг тестов** (`backend/tests/`) — отдельный audit потом, как согласовано.
- **Рефакторинг `backend/agents/`** — до Фазы 2.
- **Переписывание `useChat.ts` / `KairosProviders.tsx`** — 4.7 сказал «не трогаем», оставляем.
- **Любой рефакторинг кода, который меняет поведение наружу** (API contract, DB schema, промпт в LLM). Это audit на *внутреннюю* системность, а не смена продукта.
- **Добавление новых фич** — если в процессе сноса мёртвого кода всплывёт идея «а давайте добавим Х», она идёт в backlog, не в эту фазу.

---

## 9. Что попадёт в PROGRESS.md

Предлагаю новую **Фазу 1.6 — Системный cleanup** между 1.5 и 2. Обоснование: 1.5 (UserState) вводит новые модели БД — делать сплит `models.py` (4.6) **до** 1.5 было бы странно (мы ещё не знаем что UserState принесёт), но делать **после** 1.5 — когда models.py уже 700 строк — поздно. Решение: **4.5+4.6 сплиты делаем в этой фазе (1.6), но ПОСЛЕ 1.5.1**; остальная часть 1.6 — до 1.5.

Структура Фазы 1.6:
- 1.6.1 Инвентаризация перед сносом → `docs/ideas/from_dead_code.md`
- 1.6.2 Снос мёртвого кода (4.1, **без** crisis_situations)
- 1.6.2.5 `crisis_situations.py` → сценарии + YAML-архив (4.1.5)
- 1.6.3 `TechniqueDigest` схема (4.2)
- 1.6.4 `SelectionRule` вместо if-elif (4.3)
- 1.6.5 `AgeGroup` + `RiskLevel` enum'ы (4.10+4.11)
- 1.6.6 Карта промптов + чистка branch_a/b (4.4)
- 1.6.7 Чистка демок + ruff UP + TODO (4.8+4.9+4.12)
- 1.6.8 Сплит `auth.py` (4.5) — выполняется отдельно, можно параллельно с 1.5
- 1.6.9 Сплит `models.py` (4.6) — **после** 1.5.1 (UserState добавлен)

Остальные идеи из backlog (2, 4, 5, 7, 8, 11A, 11.1, 11.2, 12, 14) — оформляются в PROGRESS.md в отдельном заходе, по одной за раз, как просил пользователь («начать с идеи 9»).

---

## 10. Решения пользователя (Сессия 29)

1. ✅ **Scope**: все 13 находок в работу.
2. ✅ **Mort 4.1**: удалить полностью, сохранить идеи в `from_dead_code.md`.
3. ✅ **4.1.5 crisis_situations**: вариант 2 — конвертация в тестовые сценарии + YAML-архив. **Открытая тема**: как оформлять научные эталонные статьи в `knowledge_base/psychology/` — пользователь хочет отдельно обсудить при подходе к Фазе 2, сейчас не решаем.
4. ✅ **4.2 TechniqueDigest**: вариант Б — новая Pydantic-модель (обоснование через масштаб 1000 польз/день добавлено в 4.2).
5. ✅ **4.6 сплит models.py**: после 1.5.1.
6. ✅ **Audit тестов**: отдельной идеей в backlog как **не блокер**.
7. ✅ **Другие идеи из backlog (2, 4, 5, 7, 8, 11A, 11.1, 11.2, 12, 14)**: обсуждаем по одной, после Фазы 1.6.

Frontend audit и backend/agents/ audit — отложены до отдельных заходов (уже решено в разделе 1).

---

## 11. Ссылки

- Идея 9 в backlog: [`docs/ideas/backlog.md`](../../ideas/backlog.md#9-пересмотреть-модули-на-системность-исключить-кустарность)
- PROGRESS.md Фаза 1.5 (UserState): [`PROGRESS.md`](../../../PROGRESS.md#фаза-15--связующее-звено-userstate--action-loop--dev-панель-15-2-недели)
- CLAUDE.md Сессия 27 (принципы без хардкодных фраз + двухуровневые запреты)
- Design doc слоя восприятия (Сессия 18): `docs/superpowers/specs/2026-05-02-perception-layer-design.md`
- ADR Фазы 1.3 (промпт-инжиниринг из knowledge): `docs/superpowers/specs/2026-05-07-prompt-engineering-from-knowledge.md`
