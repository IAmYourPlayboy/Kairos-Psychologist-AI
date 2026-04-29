"""Детектор кризисного уровня по тексту сообщения."""

import re

from app.core.crisis.keywords import (
    ELEVATED_KEYWORDS,
    HIGH_KEYWORDS,
    IMMEDIATE_KEYWORDS,
)


def _normalize(text: str) -> str:
    """Привести текст к нижнему регистру и убрать лишние пробелы."""
    text = text.lower().strip()
    # Заменить множественные пробелы на одиночные
    text = re.sub(r"\s+", " ", text)
    # Убрать ё → е для дополнительного матчинга (оригиналы тоже в словарях)
    return text


def assess_crisis_level(text: str) -> str:
    """Оценить уровень кризиса по тексту сообщения.

    Проверяет текст на наличие ключевых слов трёх уровней угрозы.
    Возвращает наивысший обнаруженный уровень.

    Args:
        text: Текст сообщения пользователя.

    Returns:
        "immediate", "high", "elevated" или "normal".
    """
    normalized = _normalize(text)

    # Проверяем от самого серьёзного к менее серьёзному
    for keyword in IMMEDIATE_KEYWORDS:
        if keyword in normalized:
            return "immediate"

    for keyword in HIGH_KEYWORDS:
        if keyword in normalized:
            return "high"

    for keyword in ELEVATED_KEYWORDS:
        if keyword in normalized:
            return "elevated"

    return "normal"
