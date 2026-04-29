"""
Запрещённые фразы для терапевтического бота.

Этот модуль содержит список фраз, которые бот НИКОГДА не должен использовать,
так как они обесценивают чувства пользователя или неэффективны в кризисе.

Используется для:
1. Валидации промптов (тесты)
2. Проверки ответов бота (опционально, в production)
3. Обучения модели (negative examples для fine-tuning)
"""

from typing import List, Dict, Tuple
import re


# ============================================================================
# КАТЕГОРИИ ЗАПРЕЩЁННЫХ ФРАЗ
# ============================================================================

# Категория 1: Ложная эмпатия (бот не может чувствовать)
FALSE_EMPATHY = [
    "я понимаю, что ты чувствуешь",
    "я понимаю твои чувства",
    "я чувствую твою боль",
    "я знаю, каково это",
    "я переживаю за тебя",
]

# Категория 2: Обесценивание (минимизация проблемы)
INVALIDATION = [
    "всё будет хорошо",
    "всё наладится",
    "не переживай",
    "не волнуйся",
    "это пройдёт",
    "время лечит",
    "бывает и хуже",
    "могло быть хуже",
    "есть люди, которым хуже",
    "ты не один такой",
    "все через это проходят",
]

# Категория 3: Директивы (приказы, что делать)
DIRECTIVES = [
    "тебе нужно успокоиться",
    "успокойся",
    "возьми себя в руки",
    "соберись",
    "не думай об этом",
    "отвлекись",
    "просто забудь",
]

# Категория 4: Пустые фразы (не несут смысла)
EMPTY_PHRASES = [
    "держись",
    "крепись",
    "будь сильным",
    "будь сильной",
    "ты справишься",
    "у тебя всё получится",
    "верь в себя",
]

# Категория 5: Навязывание ожиданий
EXPECTATIONS = [
    "ты сильный",
    "ты сильная",
    "ты должен быть сильным",
    "ты должна быть сильной",
    "ты должен справиться",
    "от тебя многое зависит",
]

# Категория 6: Неуместные вопросы в кризисе
CRISIS_QUESTIONS = [
    "что ты чувствуешь?",  # В остром кризисе усиливает затопление
    "почему ты так себя чувствуешь?",
    "что с тобой не так?",
    "в чём проблема?",
]

# Категория 7: Токсичный позитив
TOXIC_POSITIVITY = [
    "думай позитивно",
    "настройся на позитив",
    "улыбнись",
    "радуйся жизни",
    "всё к лучшему",
    "это судьба",
    "так было нужно",
    "всё происходит не просто так",
]

# Категория 8: Сравнения и обобщения
COMPARISONS = [
    "другие справляются",
    "посмотри на других",
    "у других получается",
    "ты не первый",
    "многие через это прошли",
]

# Категория 9: Религиозные клише (если пользователь не просил)
RELIGIOUS_CLICHES = [
    "бог даёт испытания",
    "это божья воля",
    "помолись",
    "обратись к богу",
]

# Категория 10: Профессиональные границы (бот не врач/психолог)
PROFESSIONAL_BOUNDARIES = [
    "я поставлю тебе диагноз",
    "у тебя депрессия",  # Только если не из контекста пользователя
    "у тебя тревожное расстройство",
    "тебе нужны таблетки",
    "прими лекарство",
]


# ============================================================================
# ОБЪЕДИНЁННЫЙ СЛОВАРЬ
# ============================================================================

FORBIDDEN_PHRASES: Dict[str, List[str]] = {
    "false_empathy": FALSE_EMPATHY,
    "invalidation": INVALIDATION,
    "directives": DIRECTIVES,
    "empty_phrases": EMPTY_PHRASES,
    "expectations": EXPECTATIONS,
    "crisis_questions": CRISIS_QUESTIONS,
    "toxic_positivity": TOXIC_POSITIVITY,
    "comparisons": COMPARISONS,
    "religious_cliches": RELIGIOUS_CLICHES,
    "professional_boundaries": PROFESSIONAL_BOUNDARIES,
}


# ============================================================================
# ФУНКЦИИ ВАЛИДАЦИИ
# ============================================================================

def get_all_forbidden_phrases() -> List[str]:
    """
    Возвращает плоский список всех запрещённых фраз.

    Returns:
        List[str]: Список всех запрещённых фраз
    """
    all_phrases = []
    for category_phrases in FORBIDDEN_PHRASES.values():
        all_phrases.extend(category_phrases)
    return all_phrases


def contains_forbidden_phrase(text: str, case_sensitive: bool = False) -> Tuple[bool, List[Tuple[str, str]]]:
    """
    Проверяет, содержит ли текст запрещённые фразы.

    Args:
        text: Текст для проверки (обычно ответ бота)
        case_sensitive: Учитывать ли регистр (по умолчанию False)

    Returns:
        Tuple[bool, List[Tuple[str, str]]]:
            - True если найдены запрещённые фразы, False иначе
            - Список кортежей (категория, найденная_фраза)

    Example:
        >>> contains_forbidden_phrase("Я понимаю, что ты чувствуешь. Всё будет хорошо.")
        (True, [('false_empathy', 'я понимаю, что ты чувствуешь'),
                ('invalidation', 'всё будет хорошо')])
    """
    found_phrases = []

    # Нормализуем текст для проверки
    check_text = text if case_sensitive else text.lower()

    # Проверяем каждую категорию
    for category, phrases in FORBIDDEN_PHRASES.items():
        for phrase in phrases:
            check_phrase = phrase if case_sensitive else phrase.lower()

            # Используем регулярное выражение для поиска целых слов
            # \b — граница слова (чтобы не находить подстроки)
            pattern = r'\b' + re.escape(check_phrase) + r'\b'

            if re.search(pattern, check_text, re.IGNORECASE if not case_sensitive else 0):
                found_phrases.append((category, phrase))

    return (len(found_phrases) > 0, found_phrases)


def validate_prompt(prompt: str) -> Tuple[bool, str]:
    """
    Валидирует системный промпт на наличие запрещённых фраз.

    Используется в тестах для проверки, что промпты не содержат
    запрещённых паттернов.

    Args:
        prompt: Системный промпт для проверки

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
            - is_valid: True если промпт валиден, False иначе
            - error_message: Описание ошибки (пустая строка если валиден)

    Example:
        >>> is_valid, error = validate_prompt("Ты — терапевтический бот. Всё будет хорошо.")
        >>> print(is_valid, error)
        False "Промпт содержит запрещённые фразы: invalidation: 'всё будет хорошо'"
    """
    has_forbidden, found = contains_forbidden_phrase(prompt)

    if not has_forbidden:
        return (True, "")

    # Формируем сообщение об ошибке
    error_lines = ["Промпт содержит запрещённые фразы:"]
    for category, phrase in found:
        error_lines.append(f"  - {category}: '{phrase}'")

    return (False, "\n".join(error_lines))


def get_category_description(category: str) -> str:
    """
    Возвращает описание категории запрещённых фраз.

    Args:
        category: Название категории

    Returns:
        str: Описание категории
    """
    descriptions = {
        "false_empathy": "Ложная эмпатия — бот не может чувствовать",
        "invalidation": "Обесценивание — минимизация проблемы пользователя",
        "directives": "Директивы — приказы, что делать",
        "empty_phrases": "Пустые фразы — не несут смысла",
        "expectations": "Навязывание ожиданий — давление на пользователя",
        "crisis_questions": "Неуместные вопросы в кризисе — усиливают затопление",
        "toxic_positivity": "Токсичный позитив — игнорирование реальных проблем",
        "comparisons": "Сравнения — обесценивание через сравнение с другими",
        "religious_cliches": "Религиозные клише — навязывание веры",
        "professional_boundaries": "Нарушение профессиональных границ — бот не врач",
    }
    return descriptions.get(category, "Неизвестная категория")


# ============================================================================
# АЛЬТЕРНАТИВЫ (что говорить вместо запрещённых фраз)
# ============================================================================

ALTERNATIVES: Dict[str, str] = {
    # Вместо ложной эмпатии
    "я понимаю, что ты чувствуешь": "Это звучит тяжело",

    # Вместо обесценивания
    "всё будет хорошо": "Сейчас тебе тяжело. Давай разберёмся, что можно сделать прямо сейчас",
    "не переживай": "Я вижу, что тебе сейчас непросто",

    # Вместо директив
    "тебе нужно успокоиться": "Давай попробуем вместе снизить напряжение",

    # Вместо пустых фраз
    "держись": "Что тебе сейчас нужно?",

    # Вместо навязывания ожиданий
    "ты сильный": "Ты справляешься с тем, что можешь",

    # Вместо неуместных вопросов в кризисе
    "что ты чувствуешь?": "Сколько окон ты видишь вокруг себя?" (заземление),
}


def get_alternative(forbidden_phrase: str) -> str:
    """
    Возвращает альтернативную фразу вместо запрещённой.

    Args:
        forbidden_phrase: Запрещённая фраза

    Returns:
        str: Альтернативная фраза (или пустая строка, если нет альтернативы)
    """
    return ALTERNATIVES.get(forbidden_phrase.lower(), "")


# ============================================================================
# ЭКСПОРТ ДЛЯ FINE-TUNING
# ============================================================================

def export_for_finetuning() -> List[Dict[str, str]]:
    """
    Экспортирует запрещённые фразы в формате для fine-tuning.

    Формат: список negative examples для обучения модели.

    Returns:
        List[Dict[str, str]]: Список примеров в формате JSONL

    Example:
        >>> examples = export_for_finetuning()
        >>> print(examples[0])
        {
            "messages": [
                {"role": "user", "content": "мне плохо"},
                {"role": "assistant", "content": "Я понимаю, что ты чувствуешь. Всё будет хорошо."}
            ],
            "label": "negative",
            "reason": "Содержит запрещённые фразы: false_empathy, invalidation"
        }
    """
    examples = []

    # Создаём negative examples для каждой категории
    for category, phrases in FORBIDDEN_PHRASES.items():
        for phrase in phrases:
            example = {
                "messages": [
                    {"role": "user", "content": "мне плохо"},
                    {"role": "assistant", "content": phrase.capitalize() + "."}
                ],
                "label": "negative",
                "reason": f"Содержит запрещённую фразу из категории {category}: '{phrase}'",
                "category": category,
            }
            examples.append(example)

    return examples


if __name__ == "__main__":
    # Пример использования
    test_text = "Я понимаю, что ты чувствуешь. Всё будет хорошо. Держись!"

    has_forbidden, found = contains_forbidden_phrase(test_text)

    if has_forbidden:
        print(f"❌ Найдены запрещённые фразы ({len(found)}):")
        for category, phrase in found:
            print(f"  - [{category}] '{phrase}'")
            alt = get_alternative(phrase)
            if alt:
                print(f"    → Альтернатива: '{alt}'")
    else:
        print("✅ Запрещённых фраз не найдено")
