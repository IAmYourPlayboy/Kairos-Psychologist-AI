# Архитектура динамического маршрутизатора терапевтических техник

> **Концепция**: "Цель → Путь → Адаптация" (аналог Tor-мостов)
> **Версия**: 1.0 | **Дата**: Апрель 2026

---

## Философия

Система выбирает **путь через узлы (техники) к цели**, как Tor выбирает маршрут через серверы. Ключевое отличие от статического алгоритма:

- **Не "если X, то Y"** — а динамический выбор на основе контекста
- **Не жёсткий протокол** — а адаптивный маршрут с альтернативами
- **Не одна техника** — а последовательность техник до достижения цели

---

## Как это работает

### 1. Определение цели (Goal Inference)

Система **сама определяет цель** на основе состояния пользователя:

```python
def determine_goal(state: TherapyState) -> TherapyGoal:
    """
    Возможные цели:
    - REDUCE_DISTRESS: снизить острый дистресс (distress > 0.7)
    - GROUND: заземлить (диссоциация, паника)
    - REFRAME_COGNITION: изменить когнитивные паттерны (CBT)
    - ACCEPT_EMOTION: принять неизменяемое (ACT)
    - FIND_SOLUTION: помочь принять решение (SFBT)
    - REGULATE_EMOTION: научить регуляции эмоций (DBT)
    """
    
    # Кризис → стабилизация
    if state.distress_score > 0.7:
        return TherapyGoal.REDUCE_DISTRESS
    
    # Когнитивные искажения → переформулирование
    if state.theme in ["вина", "самокритика", "катастрофизация"]:
        return TherapyGoal.REFRAME_COGNITION
    
    # Борьба с неизменяемым → принятие
    if state.theme in ["утрата", "горе", "борьба"]:
        return TherapyGoal.ACCEPT_EMOTION
    
    # Застрял в проблеме → найти решение
    if state.theme in ["застрял", "не знаю что делать", "тупик"]:
        return TherapyGoal.FIND_SOLUTION
    
    # По умолчанию → снизить дистресс
    return TherapyGoal.REDUCE_DISTRESS
```

### 2. Выбор техники (Technique Selection)

Система выбирает технику из графа на основе:

1. **Цели** — техника должна подходить для текущей цели
2. **Состояния** — проверка prerequisites (например, `distress >= 0.7`)
3. **Истории** — избегает повторов (не предлагает то, что уже пробовали)
4. **Эффективности** — выбирает технику с максимальной эффективностью

```python
def choose_technique(state, goal, previous_technique):
    # Получить кандидатов для цели
    candidates = graph.get_techniques_for_goal(goal)
    
    # Отфильтровать уже использованные
    candidates = [c for c in candidates if c not in state.history]
    
    # Проверить prerequisites
    candidates = [c for c in candidates if check_prerequisites(c, state)]
    
    # Выбрать лучшего кандидата
    return max(candidates, key=lambda c: c.effectiveness_weight)
```

### 3. Построение маршрута (Route Building)

Система строит **последовательность техник** до достижения цели:

```python
def route(initial_state, user_message):
    route = []
    state = initial_state
    
    while state.attempts < state.max_attempts:
        # Определить цель
        goal = determine_goal(state)
        
        # Выбрать технику
        technique = choose_technique(state, goal, previous_technique)
        
        # Добавить в маршрут
        route.append(technique)
        state.history.append(technique.id)
        
        # Симуляция: техника снизила дистресс
        state.distress_score -= 0.15
        
        # Если цель достигнута — завершить
        if goal_achieved(goal, state):
            break
    
    return route
```

### 4. Адаптация (Adaptation)

Если техника **не работает** — система меняет путь:

```python
# В реальном диалоге:
# 1. Применили технику → оценили эффективность
# 2. Если distress не снизился → выбрать альтернативу
# 3. Альтернативы берутся из next_nodes текущей техники

if not technique_worked:
    # Получить альтернативы из графа
    alternatives = graph.get_neighbors(current_technique)
    
    # Выбрать следующую технику
    next_technique = choose_from_alternatives(alternatives, state)
```

---

## Граф терапевтических техник

Граф состоит из **узлов (техники)** и **рёбер (переходы)**:

```
[PFA заземление 5-4-3-2-1]
    ↓ (если distress снизился до 0.7)
[PFA дыхание по квадрату]
    ↓ (если distress снизился до 0.5)
[CBT переформулирование] ← или → [ACT принятие]
    ↓
[SFBT шкалирование]
```

### Узлы графа (11 техник):

| ID | Название | Категория | Цели | Prerequisites |
|----|----------|-----------|------|---------------|
| `pfa_5_4_3_2_1` | Заземление 5-4-3-2-1 | PFA | GROUND, REDUCE_DISTRESS | distress >= 0.6 |
| `pfa_box_breathing` | Дыхание по квадрату | PFA | REDUCE_DISTRESS, REGULATE_EMOTION | distress >= 0.5 |
| `dbt_tipp` | TIPP | DBT | REDUCE_DISTRESS, REGULATE_EMOTION | distress >= 0.7 |
| `dbt_radical_acceptance` | Радикальное принятие | DBT | ACCEPT_EMOTION | distress < 0.7 |
| `act_acceptance` | Принятие | ACT | ACCEPT_EMOTION | distress < 0.7 |
| `act_defusion` | Когнитивная дефузия | ACT | REFRAME_COGNITION | distress < 0.6 |
| `act_present_moment` | Контакт с настоящим | ACT | GROUND | distress >= 0.5 |
| `cbt_reframe` | Переформулирование | CBT | REFRAME_COGNITION | distress < 0.6 |
| `sfbt_miracle_question` | Вопрос о чуде | SFBT | FIND_SOLUTION | distress < 0.5 |
| `sfbt_scaling` | Шкалирование | SFBT | FIND_SOLUTION | distress < 0.6 |
| `sfbt_exceptions` | Исключения | SFBT | FIND_SOLUTION, REFRAME_COGNITION | distress < 0.6 |
| `sfbt_coping_question` | Вопрос о совладании | SFBT | FIND_SOLUTION | distress < 0.7 |

### Рёбра графа (переходы):

Каждый узел имеет `next_nodes` — список возможных следующих техник:

```python
"pfa_5_4_3_2_1": {
    next_nodes: ["pfa_box_breathing", "dbt_tipp", "act_present_moment"]
}

"pfa_box_breathing": {
    next_nodes: ["pfa_5_4_3_2_1", "dbt_tipp", "act_acceptance"]
}

"cbt_reframe": {
    next_nodes: ["act_defusion", "sfbt_scaling"]
}
```

---

## Примеры работы

### Пример 1: Кризис → Стабилизация → Переформулирование

```
User: "ПАНИКА, НЕ МОГУ ДЫШАТЬ, ВСЁ РУШИТСЯ"

Анализ:
  - distress_score = 0.85 (CAPS, паника)
  - emotion = "паника"
  - theme = "безысходность"

Маршрут:
  1. Цель: REDUCE_DISTRESS
     Техника: pfa_box_breathing (Дыхание по квадрату)
     → distress снизился до 0.70

  2. Цель: REDUCE_DISTRESS (ещё не достигнута)
     Техника: dbt_tipp (TIPP - холодная вода)
     → distress снизился до 0.55

  3. Цель: REFRAME_COGNITION (теперь можно работать с мыслями)
     Техника: cbt_reframe (Переформулирование)
     → distress снизился до 0.40

Цель достигнута!
```

### Пример 2: Техника не работает → Смена пути

```
User: "Не знаю, увольняться мне или нет"

Анализ:
  - distress_score = 0.45
  - theme = "застрял"

Маршрут:
  1. Цель: FIND_SOLUTION
     Техника: sfbt_scaling (Шкалирование)

AI: "По шкале от 1 до 10, где ты сейчас?"

User: "Не понимаю, что ты хочешь"

Адаптация:
  - sfbt_scaling не сработало
  - Альтернативы: ["sfbt_miracle_question", "sfbt_coping_question"]
  - Выбираем: sfbt_miracle_question

AI: "Давай по-другому. Представь, что завтра ты проснулся, 
     и ситуация с работой стала такой, как ты хочешь. Что изменилось?"
```

### Пример 3: Борьба с эмоцией → Принятие

```
User: "Я борюсь с тревогой, не могу от неё избавиться"

Анализ:
  - distress_score = 0.60
  - emotion = "тревога"
  - theme = "борьба"

Маршрут:
  1. Цель: ACCEPT_EMOTION
     Техника: act_acceptance (Принятие)

AI: "Звучит так, будто ты пытаешься избавиться от тревоги. 
     Что будет, если ты перестанешь бороться и позволишь ей быть здесь?"

User: "Но она мешает мне жить"

  2. Цель: ACCEPT_EMOTION (продолжаем)
     Техника: act_defusion (Когнитивная дефузия)

AI: "Замечай мысль как мысль: 'У меня есть мысль, что тревога мешает мне жить'. 
     Это мысль, не факт. Можешь ли ты жить с тревогой, не борясь с ней?"
```

---

## Интеграция с системой промптов

Маршрутизатор интегрирован в `builder.py`:

```python
from app.core.therapy_router import TherapyRouter, TherapyState

def build_system_prompt(
    branch: str,
    crisis_level: str = "normal",
    user_message: Optional[str] = None,
    distress_score: Optional[float] = None,
    emotion: Optional[str] = None,
    theme: Optional[str] = None,
    use_router: bool = True,
) -> str:
    """
    Собрать системный промпт с динамическим маршрутом техник.
    
    Если use_router=True и distress_score указан:
    - Создаётся TherapyState
    - Строится маршрут через TherapyRouter
    - Маршрут добавляется в промпт
    """
    
    if use_router and distress_score is not None:
        # Создать маршрутизатор
        router = TherapyRouter()
        
        # Создать состояние
        state = TherapyState(
            distress_score=distress_score,
            emotion=emotion,
            theme=theme,
            history=[],
            attempts=0,
        )
        
        # Построить маршрут
        route = router.route(state, user_message)
        
        # Добавить маршрут в промпт
        prompt_parts.append(format_route(route))
    
    return "\n\n".join(prompt_parts)
```

---

## Эволюция системы

### Фаза 1 (MVP, сейчас): Статический граф

- Граф с экспертными правилами (11 техник, заранее определённые связи)
- Эффективность техник — базовые значения (0.7-0.85)
- Выбор на основе правил (distress, тема, история)

### Фаза 2 (после 500+ диалогов): Обучение из данных

```python
# После каждого диалога записываем:
# - какие техники использовали
# - в каком порядке
# - насколько эффективны были переходы

# Через 500+ диалогов:
# - обновляем effectiveness_weight на основе реальных данных
# - добавляем новые связи (next_nodes), которые работают лучше
# - удаляем связи, которые не работают

def update_graph_from_data(dialogues):
    for dialogue in dialogues:
        for transition in dialogue.transitions:
            # Обновить вес эффективности
            graph[transition.from_technique].effectiveness_weight = (
                calculate_effectiveness(transition)
            )
            
            # Добавить новую связь, если она работает
            if transition.effectiveness > 0.7:
                graph[transition.from_technique].next_nodes.append(
                    transition.to_technique
                )
```

### Фаза 3 (опционально): Гибридный подход

```python
def choose_technique_hybrid(state, goal, previous_technique):
    # 1. Попробовать выбрать через граф
    graph_choice = choose_from_graph(state, goal, previous_technique)
    
    # 2. Если граф не уверен (низкая эффективность < 0.5)
    if graph_choice and graph_choice.effectiveness < 0.5:
        # Спросить LLM
        llm_choice = ask_llm_to_choose(state, goal, available_techniques)
        return llm_choice
    
    # 3. Иначе — использовать выбор графа
    return graph_choice
```

---

## Преимущества подхода

1. **Гибкость** — не жёсткий алгоритм, а динамический выбор пути
2. **Контекстность** — маршрут зависит от истории диалога
3. **Адаптивность** — если техника не работает, система меняет путь
4. **Комбинирование** — можно использовать несколько техник последовательно
5. **Обучаемость** — граф улучшается из данных (data flywheel)

---

## Файлы проекта

- `backend/app/core/therapy_router.py` — основной код маршрутизатора
- `backend/app/core/prompts/builder.py` — интеграция с системой промптов
- `backend/test_therapy_router.py` — тестовый скрипт
- `backend/app/core/knowledge/THERAPY_ROUTER_ARCHITECTURE.md` — этот файл

---

*Последнее обновление: Апрель 2026*
