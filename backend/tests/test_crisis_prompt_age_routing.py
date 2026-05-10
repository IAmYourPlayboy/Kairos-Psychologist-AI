"""Тесты возрастной маршрутизации кризисных контактов в промпте (Фаза 0.5, Сессия 27).

Цель: гарантировать что при `age_group="adult"` промпт основной LLM
НЕ содержит детского телефона доверия, и наоборот для `age_group="child"`.
Баг который это ловит (S03, S04 в Фазе 0.1): до Сессии 27 телефон
8-800-2000-122 (Детский телефон доверия) был ЖЁСТКО ЗАШИТ в prompts/crisis.py,
попадал в ответы бота для adult-пользователей независимо от age_group в запросе.

Также проверяем принцип «без хардкодных фраз» (CLAUDE.md, Сессия 27):
в промпте НЕТ буквальных фраз ответа бота — только протокол, запреты, данные, формат.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./kairos_test_default.db")
os.environ.setdefault("LLM_API_KEY", "test-key")

import pytest

from app.core.crisis.contacts import (
    ADULT_CONTACTS,
    CHILD_CONTACTS,
    UNIVERSAL_CONTACTS,
    YOUTH_CONTACTS,
    format_contacts_for_prompt,
    get_crisis_contacts,
)
from app.core.prompts.crisis import build_crisis_prompt


# Константы-маркеры (чтобы в тестах не повторять магические строки)
CHILD_HOTLINE = "8-800-2000-122"  # Детский телефон доверия (до 18)
YOUTH_HOTLINE = "8-800-100-49-94"  # «Помощь рядом» (до 25)
ADULT_HOTLINE = "8-800-700-84-60"  # Линия «0-24» (25+)
MCHS_HOTLINE = "8-800-333-44-34"  # МЧС (универсальный)
EMERGENCY = "112"  # 112 (универсальный)


# ============================================================================
# format_contacts_for_prompt
# ============================================================================


def test_format_contacts_adult_no_child_hotline():
    """Главное свойство фикса Сессии 27: adult не видит детский телефон."""
    text = format_contacts_for_prompt("adult")
    assert CHILD_HOTLINE not in text, (
        "Детский телефон 8-800-2000-122 попал в промпт для adult. "
        "Это тот самый баг S03/S04 Фазы 0.1, который мы чиним."
    )
    # Взрослая линия должна быть
    assert ADULT_HOTLINE in text
    # И универсальные тоже
    assert EMERGENCY in text
    assert MCHS_HOTLINE in text


def test_format_contacts_child_includes_child_hotline():
    text = format_contacts_for_prompt("child")
    assert CHILD_HOTLINE in text
    # Молодёжная тоже (14-18 могут попадать в оба)
    assert YOUTH_HOTLINE in text
    # Адресованный взрослым — НЕ нужен
    assert ADULT_HOTLINE not in text
    # Универсальные есть
    assert EMERGENCY in text


def test_format_contacts_youth_includes_youth_and_adult():
    text = format_contacts_for_prompt("youth")
    assert YOUTH_HOTLINE in text
    assert ADULT_HOTLINE in text
    # Детский — НЕ нужен (ребёнок и подросток — разные возрастные группы)
    assert CHILD_HOTLINE not in text


def test_format_contacts_none_includes_all():
    """Без указания возраста — консервативный дефолт: все контакты."""
    text = format_contacts_for_prompt(None)
    assert CHILD_HOTLINE in text
    assert YOUTH_HOTLINE in text
    assert ADULT_HOTLINE in text


def test_format_contacts_has_one_per_line():
    """Каждый контакт на отдельной строке (ФОРМАТ ВЫВОДА из crisis.py)."""
    text = format_contacts_for_prompt("adult")
    lines = [ln for ln in text.split("\n") if ln.strip()]
    # Каждая строка начинается с "- " (дефис-маркер списка)
    for line in lines:
        assert line.startswith("- "), f"Строка не в формате списка: {line!r}"
    # Минимум 3 контакта для adult (112 + МЧС + 0-24)
    assert len(lines) >= 3


def test_format_contacts_no_emoji():
    """Эмодзи запрещены (ФОРМАТ ВЫВОДА). До Сессии 27 промпт содержал 📞."""
    text = format_contacts_for_prompt("adult")
    assert "📞" not in text
    assert "☎" not in text
    # Простая проверка на отсутствие популярных эмодзи-диапазонов
    for ch in text:
        assert ord(ch) < 0x1F000, f"Найден эмодзи {ch!r} в тексте контактов"


# ============================================================================
# build_crisis_prompt: возрастная маршрутизация
# ============================================================================


@pytest.mark.parametrize("level", ["elevated", "high", "immediate"])
def test_build_crisis_prompt_adult_no_child_hotline(level):
    """Регрессия на S03/S04: adult не получает детский телефон ни на каком уровне кризиса."""
    prompt = build_crisis_prompt(level, age_group="adult")
    assert prompt is not None
    assert CHILD_HOTLINE not in prompt, (
        f"На уровне {level} для adult детский телефон {CHILD_HOTLINE} "
        f"попал в промпт. Это баг S03/S04 из Фазы 0.1."
    )
    assert ADULT_HOTLINE in prompt


@pytest.mark.parametrize("level", ["elevated", "high", "immediate"])
def test_build_crisis_prompt_child_has_child_hotline(level):
    prompt = build_crisis_prompt(level, age_group="child")
    assert prompt is not None
    assert CHILD_HOTLINE in prompt
    assert ADULT_HOTLINE not in prompt


def test_build_crisis_prompt_normal_returns_none_for_all_ages():
    for age in ("child", "youth", "adult", None):
        assert build_crisis_prompt("normal", age_group=age) is None


# ============================================================================
# Принцип «без хардкодных фраз» (CLAUDE.md, Сессия 27)
# ============================================================================


_OLD_HARDCODED_PHRASES = [
    # Из старой версии crisis.py (до Сессии 27) — буквальный текст ответа бота.
    # Теперь такие фразы в промпт не попадают, LLM формулирует сама.
    "Я слышу тебя",
    "Прямо сейчас позвони",
    "Там помогут",
    "Я буду здесь, когда вернёшься",
    "Есть люди, которые помогают именно в таких ситуациях",
]


@pytest.mark.parametrize("level", ["elevated", "high", "immediate"])
@pytest.mark.parametrize("age", ["child", "youth", "adult", None])
def test_build_crisis_prompt_no_hardcoded_example_phrases(level, age):
    """В промпте нет буквальных примеров фраз-шаблонов ответа бота."""
    prompt = build_crisis_prompt(level, age_group=age)
    assert prompt is not None
    for phrase in _OLD_HARDCODED_PHRASES:
        assert phrase not in prompt, (
            f"Найдена захардкоденная фраза из до-Сессия-27 crisis.py: {phrase!r}. "
            f"Принцип «без хардкодных фраз» нарушен (см. CLAUDE.md)."
        )


@pytest.mark.parametrize("level", ["elevated", "high", "immediate"])
def test_build_crisis_prompt_no_emoji(level):
    prompt = build_crisis_prompt(level, age_group="adult")
    assert "📞" not in prompt
    assert "☎" not in prompt


# ============================================================================
# Структурные элементы промпта (что должно быть — протокол + запреты + формат)
# ============================================================================


def test_build_crisis_prompt_contains_protocol_block():
    for level, marker in (
        ("elevated", "ПОВЫШЕННЫЙ"),
        ("high", "ВЫСОКИЙ"),
        ("immediate", "НЕМЕДЛЕННЫЙ"),
    ):
        prompt = build_crisis_prompt(level, age_group="adult")
        assert marker in prompt, f"Нет протокольного заголовка {marker} на уровне {level}"


def test_build_crisis_prompt_contains_forbidden_phrases_block():
    prompt = build_crisis_prompt("immediate", age_group="adult")
    assert "ЗАПРЕЩЁННЫЕ ФРАЗЫ" in prompt
    # Несколько ключевых запретов присутствуют
    assert "Держись" in prompt
    assert "Я понимаю" in prompt or "«Я понимаю" in prompt


def test_build_crisis_prompt_contains_format_block():
    prompt = build_crisis_prompt("immediate", age_group="adult")
    assert "ФОРМАТ ВЫВОДА" in prompt
    assert "эмодзи" in prompt.lower()


def test_build_crisis_prompt_contains_contacts_data_block():
    prompt = build_crisis_prompt("high", age_group="adult")
    assert "КРИЗИСНЫЕ КОНТАКТЫ" in prompt


# ============================================================================
# Контракт get_crisis_contacts (база, на которой стоит format_contacts_for_prompt)
# ============================================================================


def test_get_crisis_contacts_universal_always_included():
    for age in ("child", "youth", "adult", None):
        contacts = get_crisis_contacts(age)
        phones = {c.phone for c in contacts}
        for uc in UNIVERSAL_CONTACTS:
            assert uc.phone in phones, (
                f"Универсальный контакт {uc.phone} не попал для age={age}"
            )


def test_get_crisis_contacts_adult_does_not_include_child_list():
    contacts = get_crisis_contacts("adult")
    phones = {c.phone for c in contacts}
    for cc in CHILD_CONTACTS:
        assert cc.phone not in phones


def test_get_crisis_contacts_child_does_not_include_adult_list():
    contacts = get_crisis_contacts("child")
    phones = {c.phone for c in contacts}
    for ac in ADULT_CONTACTS:
        assert ac.phone not in phones
