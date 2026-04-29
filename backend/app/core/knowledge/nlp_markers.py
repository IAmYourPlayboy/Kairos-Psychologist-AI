"""
База знаний: Лингвистические маркеры дистресса (NLP Layer 1).

Этот модуль содержит rule-based маркеры для определения уровня дистресса
по лингвистическим паттернам в тексте пользователя.

Используется в: app/core/nlp/markers.py
"""

from typing import Dict, List, Tuple
import re


# ============================================================================
# КАТЕГОРИЯ 1: АБСОЛЮТИСТСКАЯ ЛЕКСИКА
# ============================================================================

ABSOLUTIST_WORDS = [
    # Русские абсолютизмы
    "никогда",
    "всегда",
    "никто",
    "все",
    "ничего",
    "всё",
    "никак",
    "невозможно",
    "бесполезно",
    "безнадёжно",
    "навсегда",
    "постоянно",
    "вечно",
    "абсолютно",
    "полностью",
    "совершенно",
    "окончательно",
]

# Вес: высокий (0.3 за каждое слово)
ABSOLUTIST_WEIGHT = 0.3


# ============================================================================
# КАТЕГОРИЯ 2: ОТСУТСТВИЕ БУДУЩЕГО ВРЕМЕНИ
# ============================================================================

# Маркеры будущего времени (их отсутствие = дистресс)
FUTURE_MARKERS = [
    # Глаголы будущего времени
    r"\bбуду\b",
    r"\bбудешь\b",
    r"\bбудет\b",
    r"\bбудем\b",
    r"\bбудете\b",
    r"\bбудут\b",

    # Планы
    r"\bпланирую\b",
    r"\bсобираюсь\b",
    r"\bхочу\b",
    r"\bнадеюсь\b",
    r"\bмечтаю\b",

    # Временные маркеры будущего
    r"\bзавтра\b",
    r"\bпотом\b",
    r"\bскоро\b",
    r"\bвскоре\b",
    r"\bпозже\b",
    r"\bв будущем\b",
    r"\bчерез\b",
]

# Вес: средний (0.2 если нет будущего времени)
NO_FUTURE_WEIGHT = 0.2


# ============================================================================
# КАТЕГОРИЯ 3: СОКРАЩЕНИЕ СООБЩЕНИЙ
# ============================================================================

# Минимальная длина "нормального" сообщения (в словах)
MIN_NORMAL_LENGTH = 5

# Вес: низкий (0.1 за короткое сообщение)
SHORT_MESSAGE_WEIGHT = 0.1


# ============================================================================
# КАТЕГОРИЯ 4: CAPS LOCK (крик, отчаяние)
# ============================================================================

# Процент заглавных букв для срабатывания
CAPS_THRESHOLD = 0.5  # 50% текста заглавными

# Вес: средний (0.2)
CAPS_WEIGHT = 0.2


# ============================================================================
# КАТЕГОРИЯ 5: МАТ И СЛЕНГ (маркеры дистресса, не агрессии)
# ============================================================================

DISTRESS_SLANG = [
    # Мат как маркер дистресса (не агрессии)
    r"\bп[иы]зд",
    r"\bбл[яь]",
    r"\bх[уy]",
    r"\bеб",

    # Сленг отчаяния
    r"\bпздц\b",
    r"\bхз\b",
    r"\bпох\b",
    r"\bнах\b",
    r"\bзае",
]

# Вес: низкий (0.1 за каждое слово)
SLANG_WEIGHT = 0.1


# ============================================================================
# КАТЕГОРИЯ 6: ПАССИВНЫЕ КОНСТРУКЦИИ
# ============================================================================

PASSIVE_MARKERS = [
    # "Со мной происходит" вместо "Я делаю"
    r"\bсо мной\b",
    r"\bмне кажется\b",
    r"\bя не могу\b",
    r"\bу меня не получается\b",
    r"\bне выходит\b",
    r"\bне получается\b",
]

# Вес: низкий (0.1)
PASSIVE_WEIGHT = 0.1


# ============================================================================
# КАТЕГОРИЯ 7: БЕЗЫСХОДНОСТЬ (КРАСНАЯ ЗОНА)
# ============================================================================

HOPELESSNESS_MARKERS = [
    "бессмысленно",
    "нет смысла",
    "зачем",
    "какой смысл",
    "не вижу смысла",
    "нет выхода",
    "безвыходно",
    "тупик",
    "конец",
    "всё кончено",
]

# Вес: критический (0.5)
HOPELESSNESS_WEIGHT = 0.5


# ============================================================================
# ФУНКЦИИ АНАЛИЗА
# ============================================================================

def calculate_distress_score(text: str) -> Tuple[float, Dict[str, float]]:
    """
    Вычисляет distress_score на основе лингвистических маркеров.

    Args:
        text: Текст сообщения пользователя

    Returns:
        Tuple[float, Dict[str, float]]:
            - distress_score (0.0-1.0)
            - breakdown по категориям

    Example:
        >>> score, breakdown = calculate_distress_score("НИКОГДА НЕ ПОЛУЧИТСЯ БЛЯТЬ")
        >>> print(f"Score: {score:.2f}")
        Score: 0.70
        >>> print(breakdown)
        {'absolutist': 0.3, 'caps': 0.2, 'slang': 0.1, 'no_future': 0.2}
    """
    breakdown = {}
    total_score = 0.0

    # Нормализуем текст
    text_lower = text.lower()
    words = text_lower.split()
    word_count = len(words)

    # 1. Абсолютистская лексика
    absolutist_count = sum(1 for word in ABSOLUTIST_WORDS if word in text_lower)
    if absolutist_count > 0:
        absolutist_score = min(absolutist_count * ABSOLUTIST_WEIGHT, 0.5)
        breakdown['absolutist'] = absolutist_score
        total_score += absolutist_score

    # 2. Отсутствие будущего времени
    has_future = any(re.search(marker, text_lower) for marker in FUTURE_MARKERS)
    if not has_future and word_count >= MIN_NORMAL_LENGTH:
        breakdown['no_future'] = NO_FUTURE_WEIGHT
        total_score += NO_FUTURE_WEIGHT

    # 3. Короткое сообщение
    if word_count < MIN_NORMAL_LENGTH:
        breakdown['short_message'] = SHORT_MESSAGE_WEIGHT
        total_score += SHORT_MESSAGE_WEIGHT

    # 4. CAPS LOCK
    if len(text) > 0:
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
        if caps_ratio >= CAPS_THRESHOLD:
            breakdown['caps'] = CAPS_WEIGHT
            total_score += CAPS_WEIGHT

    # 5. Мат и сленг
    slang_count = sum(1 for pattern in DISTRESS_SLANG if re.search(pattern, text_lower))
    if slang_count > 0:
        slang_score = min(slang_count * SLANG_WEIGHT, 0.3)
        breakdown['slang'] = slang_score
        total_score += slang_score

    # 6. Пассивные конструкции
    passive_count = sum(1 for pattern in PASSIVE_MARKERS if re.search(pattern, text_lower))
    if passive_count > 0:
        passive_score = min(passive_count * PASSIVE_WEIGHT, 0.2)
        breakdown['passive'] = passive_score
        total_score += passive_score

    # 7. Безысходность (КРАСНАЯ ЗОНА)
    hopelessness_count = sum(1 for marker in HOPELESSNESS_MARKERS if marker in text_lower)
    if hopelessness_count > 0:
        hopelessness_score = min(hopelessness_count * HOPELESSNESS_WEIGHT, 0.7)
        breakdown['hopelessness'] = hopelessness_score
        total_score += hopelessness_score

    # Ограничиваем score диапазоном [0.0, 1.0]
    final_score = min(total_score, 1.0)

    return (final_score, breakdown)


def get_distress_level(score: float) -> str:
    """
    Преобразует distress_score в уровень.

    Args:
        score: Distress score (0.0-1.0)

    Returns:
        str: "low", "moderate", "high", "critical"
    """
    if score < 0.3:
        return "low"
    elif score < 0.6:
        return "moderate"
    elif score < 0.8:
        return "high"
    else:
        return "critical"


if __name__ == "__main__":
    # Примеры использования
    test_cases = [
        "Привет, как дела?",
        "мне плохо",
        "НИКОГДА НЕ ПОЛУЧИТСЯ",
        "всё бессмысленно, нет выхода",
        "хз что делать, пздц просто",
    ]

    for text in test_cases:
        score, breakdown = calculate_distress_score(text)
        level = get_distress_level(score)
        print(f"\nТекст: '{text}'")
        print(f"Score: {score:.2f} ({level})")
        print(f"Breakdown: {breakdown}")
