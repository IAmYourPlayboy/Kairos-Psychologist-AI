# База знаний AI-Психолог

> **Назначение**: Структурированные данные для терапевтических техник и NLP-анализа

---

## 📁 Структура

```
backend/app/core/knowledge/
├── nlp_markers.py .............. Лингвистические маркеры дистресса (rule-based)
├── cbt_techniques.py ........... CBT техники и когнитивные искажения
├── dbt_skills.py ............... DBT навыки (4 модуля)
├── act_processes.py ............ ACT процессы (Hexaflex)
├── who_pfa.py .................. ВОЗ PFA (Первая психологическая помощь)
├── sfbt_mi.py .................. SFBT + Мотивационное консультирование
├── THERAPEUTIC_KNOWLEDGE_BASE.md  Сводный справочник всех подходов
└── README.md ................... Этот файл
```

---

## 🎯 Как использовать

### 1. NLP маркеры (nlp_markers.py)

**Назначение**: Определение уровня дистресса по лингвистическим паттернам.

```python
from app.core.knowledge.nlp_markers import calculate_distress_score, get_distress_level

text = "НИКОГДА НЕ ПОЛУЧИТСЯ, всё бессмысленно"
score, breakdown = calculate_distress_score(text)
level = get_distress_level(score)

print(f"Score: {score:.2f} ({level})")
# Score: 0.80 (critical)
print(breakdown)
# {'absolutist': 0.3, 'hopelessness': 0.5, 'caps': 0.2}
```

**Используется в**: `app/core/nlp/markers.py` (Слой 1 двухслойного NLP)

---

### 2. CBT техники (cbt_techniques.py)

**Назначение**: Когнитивные искажения и техники переформулирования.

```python
from app.core.knowledge.cbt_techniques import get_distortion_by_keywords, COGNITIVE_DISTORTIONS

text = "Я всегда всё порчу. Я неудачник."
distortions = get_distortion_by_keywords(text)
# ['all_or_nothing', 'labeling']

for dist_key in distortions:
    dist = COGNITIVE_DISTORTIONS[dist_key]
    print(f"{dist.name}: {dist.reframe_technique}")
```

**Используется в**: `app/core/prompts/builder.py` (терапевтический режим)

---

### 3. DBT навыки (dbt_skills.py)

**Назначение**: 4 модуля DBT (осознанность, дистресс-толерантность, регуляция эмоций, межличностная эффективность).

```python
from app.core.knowledge.dbt_skills import suggest_dbt_skill, ALL_DBT_SKILLS

situation = "У меня паническая атака, сердце бьётся"
skills = suggest_dbt_skill(situation)
# ['tipp']

skill = ALL_DBT_SKILLS['tipp']
print(skill.steps)
# ['T (Temperature): холодная вода на лицо', ...]
```

**Используется в**: `app/core/prompts/builder.py` (терапевтический режим)

---

### 4. ACT процессы (act_processes.py)

**Назначение**: 6 процессов ACT (Hexaflex) с метафорами.

```python
from app.core.knowledge.act_processes import suggest_act_process, ACT_PROCESSES, ACT_METAPHORS

situation = "Я борюсь с тревогой, не могу от неё избавиться"
processes = suggest_act_process(situation)
# ['acceptance', 'cognitive_defusion']

process = ACT_PROCESSES['acceptance']
print(process.metaphor)
# "Борьба с зыбучим песком — чем больше борешься, тем глубже тонешь..."
```

**Используется в**: `app/core/prompts/builder.py` (терапевтический режим)

---

### 5. ВОЗ PFA (who_pfa.py)

**Назначение**: Первая психологическая помощь по протоколам Всемирной организации здравоохранения.

```python
from app.core.knowledge.who_pfa import suggest_pfa_technique, get_pfa_technique

situation = "паника, не могу дышать"
techniques = suggest_pfa_technique(situation)
# ['box_breathing', '5_4_3_2_1']

technique = get_pfa_technique("5_4_3_2_1")
print(technique.steps)
# ['5 вещей, которые ты ВИДИШЬ', '4 вещи, которые ты можешь ПОТРОГАТЬ', ...]
```

**Используется в**: `app/core/prompts/builder.py` (кризисный режим)

---

### 6. SFBT + Мотивационное консультирование (sfbt_mi.py)

**Назначение**: ОРКТ (Ориентированная на решение краткосрочная терапия) + Мотивационное консультирование (OARS).

```python
from app.core.knowledge.sfbt_mi import suggest_sfbt_technique, get_sfbt_technique, get_mi_by_category

# SFBT
situation = "не знаю, что делать, всё плохо"
techniques = suggest_sfbt_technique(situation)
# ['miracle_question', 'scaling']

technique = get_sfbt_technique("miracle_question")
print(technique.example_question)
# "Представь, что ночью произошло чудо..."

# Мотивационное консультирование
reflections = get_mi_by_category("reflect")
print(list(reflections.keys()))
# ['simple', 'complex', 'amplified']
```

**Используется в**: `app/core/prompts/builder.py` (терапевтический режим)

---

## 🔗 Связь со скиллами

Эта база знаний — **реализация** следующих скиллов:

| Скилл (документация) | Модуль (код) |
|----------------------|--------------|
| `skills/nlp-emotion-analysis.md` | `nlp_markers.py` |
| `skills/therapeutic-prompts.md` | `cbt_techniques.py`, `dbt_skills.py`, `act_processes.py` |
| `skills/crisis-routing.md` | `nlp_markers.py` (distress score) |

---

## 📝 Дополнение базы знаний

**Перед добавлением новых данных**:
1. Проверь с психологом (РГСУ)
2. Добавь источники (научные статьи, протоколы)
3. Напиши тесты для новых техник

**Формат**:
- Используй `@dataclass` для структурированных данных
- Добавляй примеры использования в `if __name__ == "__main__"`
- Документируй каждую функцию (docstring)

---

## 🧪 Тестирование

```bash
# Запустить все модули для проверки
python -m app.core.knowledge.nlp_markers
python -m app.core.knowledge.cbt_techniques
python -m app.core.knowledge.dbt_skills
python -m app.core.knowledge.act_processes
```

---

*Последнее обновление: Апрель 2026*
