"""Глобальные fixtures для pytest.

Запуск тестов:
    cd backend
    pytest                      # все тесты
    pytest tests/test_crisis.py # один файл
    pytest -k "crisis"          # по имени
    pytest -v                   # подробный вывод
"""

import sys
from pathlib import Path

import pytest

# Добавляем корень backend в sys.path, чтобы импорты "from app..." работали
BACKEND_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture
def sample_crisis_messages() -> dict[str, list[str]]:
    """Примеры сообщений по уровням кризиса для тестов детектора."""
    return {
        "immediate": [
            "хочу умереть",
            "покончить с собой",
            "не хочу жить",
        ],
        "high": [
            "всё бессмысленно",
            "нет выхода",
            "я в тупике",
        ],
        "elevated": [
            "мне плохо",
            "не могу больше",
            "тяжело",
        ],
        "normal": [
            "привет",
            "как дела",
            "просто хочу поговорить",
        ],
    }


@pytest.fixture
def forbidden_phrases() -> list[str]:
    """Фразы, которые бот НИКОГДА не должен произносить."""
    return [
        "Всё будет хорошо",
        "Держись",
        "Я понимаю, что ты чувствуешь",
        "Тебе нужно успокоиться",
        "Бывает и хуже",
        "Ты сильный",
        "Ты сильная",
        "Что ты чувствуешь?",
        "Успокойся",
        "Не переживай",
        "Время лечит",
        "Всё наладится",
    ]
