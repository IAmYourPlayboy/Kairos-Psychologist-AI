"""Промпты для ReflectionAgent (Фаза 5).

Два этапа имеют свои промпты:
- EXTRACT: извлечение фактов-кандидатов из необработанного хвоста разговора.
- DEDUPE: семантическое сравнение факта-кандидата с существующими.

Список папок для extract-промпта генерируется из folders.py
(единый источник правды). Критерии «как распознать триггер» — из
``knowledge/digests.py::CBT_TRIGGERS`` и ``DBT_TRIGGERS`` (Сессия 23,
Фаза 1.3 — выжимка из CBT/DBT в reflection-агента).

Дизайн:

- §7 в исходной spec слоя восприятия (Сессия 18).
- ``docs/superpowers/specs/2026-05-07-prompt-engineering-from-knowledge.md``
  (Сессия 23) — почему сюда подмешиваются критерии триггеров.
"""

from app.core.knowledge.digests import CBT_TRIGGERS, DBT_TRIGGERS
from app.core.perception.folders import render_parent_child_pairs_for_prompt

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
4. Если факт может попасть в несколько папок — выбрать ОДНУ, основную.
5. Для пользовательских (custom) папок — давать осмысленное английское имя \
   (medical_visits, army_recruitment), не транскрипцию русского.
6. Возвращать строго валидный JSON-массив. Без объяснений вне JSON.

ВАЖНО — РАЗДЕЛЕНИЕ folder и subfolder:
candidate_folder и candidate_subfolder — это ДВА РАЗНЫХ ПОЛЯ.
НИКОГДА не пиши "family/siblings" в candidate_folder — это ОШИБКА.
Правильно: candidate_folder = "family", candidate_subfolder = "siblings".
В таблице ниже формат "родитель/потомок" — это просто список допустимых ПАР,
а не одно значение. Каждую такую пару записывай в JSON как ДВЕ строки.

Допустимые ПАРЫ (родитель → потомок):
{{PARENT_CHILD_PAIRS}}

ПРАВИЛЬНЫЙ пример факта:
{
  "summary": "Есть младший брат Егор",
  "candidate_folder": "family",
  "candidate_subfolder": "siblings",
  "candidate_tags": ["younger-brother", "egor"],
  "severity": 0.2,
  "confidence": 0.95,
  "quotes": [{"message_id": "msg-001", "text": "у меня есть младший брат Егор"}]
}

НЕПРАВИЛЬНЫЙ пример (НЕ ДЕЛАЙ ТАК):
{
  "candidate_folder": "family/siblings",  // СКЛЕИЛ через слэш — НЕЛЬЗЯ
  "candidate_subfolder": null
}

{{CBT_TRIGGERS}}

{{DBT_TRIGGERS}}

Структура каждого факта в выходном JSON-массиве:
{
  "summary": str (1-2 предложения),
  "candidate_folder": str (ТОЛЬКО ОДНО СЛОВО из списка родителей выше: "family", "health", "routines" и т.д. — БЕЗ слэша),
  "candidate_subfolder": str | null (ТОЛЬКО ОДНО СЛОВО — потомок из списка для этого родителя, ИЛИ null если родитель его не требует),
  "candidate_tags": [str, ...] (kebab-case, до 5),
  "severity": float (0.0-1.0),
  "confidence": float (0.0-1.0 — насколько ты уверен),
  "quotes": [
    {"message_id": str, "text": str (буквальная фраза пользователя)},
    ...
  ]
}

Если фактов нет — верни пустой массив [].

Никакого текста вне JSON. Только сырой JSON-массив.
"""

# Подставляем актуальный список папок из folders.py — единый источник правды.
EXTRACT_SYSTEM_PROMPT = EXTRACT_SYSTEM_PROMPT.replace(
    "{{PARENT_CHILD_PAIRS}}",
    render_parent_child_pairs_for_prompt(),
)

# Подставляем выжимки про триггеры из digests.py.
# CBT_TRIGGERS — когнитивные искажения как маркер устойчивого триггера.
# DBT_TRIGGERS — эмоциональная дисрегуляция + отличие от разовой реакции.
# Цель: extract-агент извлекает не «настроение дня», а устойчивые паттерны.
EXTRACT_SYSTEM_PROMPT = EXTRACT_SYSTEM_PROMPT.replace(
    "{{CBT_TRIGGERS}}",
    CBT_TRIGGERS,
).replace(
    "{{DBT_TRIGGERS}}",
    DBT_TRIGGERS,
)


def build_extract_user_prompt(
    *,
    messages_block: str,
    existing_dossier_summary: str,
) -> str:
    """Собрать user-prompt для extract-этапа.

    Args:
        messages_block: текстовый блок сообщений пользователя в хронологическом
                        порядке с message_id рядом с каждым.
        existing_dossier_summary: компактная выжимка существующего досье
                                  (чтобы агент не дублировал то, что уже есть).
    """
    return (
        f"## ТЕКУЩЕЕ ДОСЬЕ ПОЛЬЗОВАТЕЛЯ (для ориентира — что уже знаем):\n"
        f"{existing_dossier_summary}\n\n"
        f"## НЕОБРАБОТАННЫЕ СООБЩЕНИЯ ПОЛЬЗОВАТЕЛЯ:\n"
        f"{messages_block}\n\n"
        f"Извлеки факты по схеме. Только JSON-массив."
    )


# ============================================================================
# DEDUPE этап
# ============================================================================


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
- "merge"        — слить с факт-id (тот же факт, добавить цитату).
- "create_new"   — создать новый факт с нуля.
- "supersede"    — создать новый, пометить старый как устаревший.

Верни строго валидный JSON:
{
  "decision": "merge" | "create_new" | "supersede",
  "target_fact_id": str | null  (id существующего факта для merge или supersede)
}

Никакого текста вне JSON.
"""


def build_dedupe_user_prompt(
    *,
    candidate_summary: str,
    candidate_quotes: list[str],
    existing_facts: list[dict],
) -> str:
    """Собрать user-prompt для dedupe-этапа."""
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
