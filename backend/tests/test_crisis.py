"""Тесты кризисной детекции (Блок 4)."""

import pytest

from app.core.crisis.contacts import CrisisContact, get_crisis_contacts
from app.core.crisis.detector import assess_crisis_level
from app.core.crisis.keywords import (
    ELEVATED_KEYWORDS,
    HIGH_KEYWORDS,
    IMMEDIATE_KEYWORDS,
)


# --- Детектор: immediate ---


@pytest.mark.parametrize(
    "text",
    [
        "хочу умереть",
        "Хочу умереть",
        "я ХОЧУ УМЕРЕТЬ",
        "не хочу жить",
        "покончить с собой",
        "суицид",
        "нет смысла жить",
        "устал жить",
        "лучше бы меня не было",
    ],
)
def test_immediate_detection(text: str):
    assert assess_crisis_level(text) == "immediate"


def test_immediate_in_context():
    """Ключевые слова работают внутри длинного сообщения."""
    assert assess_crisis_level("я больше не могу, хочу умереть, помогите") == "immediate"


# --- Детектор: high ---


@pytest.mark.parametrize(
    "text",
    [
        "нет выхода",
        "никто не поможет",
        "никому не нужен",
        "всем будет лучше без меня",
        "хочу исчезнуть",
        "больше не выдержу",
        "никогда не станет лучше",
    ],
)
def test_high_detection(text: str):
    assert assess_crisis_level(text) == "high"


# --- Детектор: elevated ---


@pytest.mark.parametrize(
    "text",
    [
        "паника",
        "паническая атака",
        "не могу дышать",
        "трясёт",
        "мне очень плохо",
        "схожу с ума",
        "ненавижу себя",
        "невыносимо",
    ],
)
def test_elevated_detection(text: str):
    assert assess_crisis_level(text) == "elevated"


# --- Детектор: normal ---


@pytest.mark.parametrize(
    "text",
    [
        "привет",
        "как дела",
        "мне грустно",
        "сегодня тяжёлый день",
        "поссорился с другом",
        "не выспался",
        "",
    ],
)
def test_normal_detection(text: str):
    assert assess_crisis_level(text) == "normal"


# --- Приоритет уровней ---


def test_immediate_takes_priority_over_high():
    """Если есть и immediate, и high маркеры — возвращаем immediate."""
    text = "нет выхода, хочу умереть"
    assert assess_crisis_level(text) == "immediate"


def test_high_takes_priority_over_elevated():
    """Если есть и high, и elevated маркеры — возвращаем high."""
    text = "паника, никто не поможет"
    assert assess_crisis_level(text) == "high"


# --- Нормализация ---


def test_case_insensitive():
    assert assess_crisis_level("ХОЧУ УМЕРЕТЬ") == "immediate"


def test_extra_whitespace():
    assert assess_crisis_level("  хочу   умереть  ") == "immediate"


# --- Словари не пустые ---


def test_keywords_not_empty():
    assert len(IMMEDIATE_KEYWORDS) >= 10
    assert len(HIGH_KEYWORDS) >= 10
    assert len(ELEVATED_KEYWORDS) >= 10


# --- Контакты ---


def test_universal_contacts_always_present():
    contacts = get_crisis_contacts()
    phones = [c.phone for c in contacts]
    assert "112" in phones
    assert "8-800-333-44-34" in phones


def test_child_contacts():
    contacts = get_crisis_contacts("child")
    phones = [c.phone for c in contacts]
    assert "8-800-2000-122" in phones  # Детский телефон доверия


def test_youth_contacts():
    contacts = get_crisis_contacts("youth")
    phones = [c.phone for c in contacts]
    assert "8-800-100-49-94" in phones  # Помощь рядом


def test_adult_contacts():
    contacts = get_crisis_contacts("adult")
    phones = [c.phone for c in contacts]
    assert "8-800-700-84-60" in phones  # Линия 0-24


def test_none_returns_all():
    contacts = get_crisis_contacts(None)
    assert len(contacts) >= 5  # Все группы


def test_contact_is_pydantic_model():
    contacts = get_crisis_contacts()
    assert all(isinstance(c, CrisisContact) for c in contacts)
