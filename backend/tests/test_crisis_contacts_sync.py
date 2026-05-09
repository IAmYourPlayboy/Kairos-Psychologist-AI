"""Sync-тест: frontend/lib/crisis-contacts.ts ↔ backend/app/core/crisis/contacts.py.

Принцип Сессии 18: SOS работает даже при сбое analyzer/backend, поэтому
контакты дублируются на frontend. Этот тест ловит расхождение между
двумя источниками — если кто-то поменял номер только в одном месте.

Технически: парсим TypeScript-файл регулярным выражением, извлекаем все
телефоны, сравниваем с множеством телефонов из contacts.py.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.core.crisis.contacts import (
    ADULT_CONTACTS,
    CHILD_CONTACTS,
    MOSCOW_CONTACTS,
    UNIVERSAL_CONTACTS,
    YOUTH_CONTACTS,
)

# Путь к frontend-файлу относительно корня репозитория
# tests/ -> backend/ -> repo-root/ -> frontend/lib/crisis-contacts.ts
FRONTEND_FILE = (
    Path(__file__).parent.parent.parent / "frontend" / "lib" / "crisis-contacts.ts"
)

# Регулярка для извлечения phone: "..." из TypeScript объектов
PHONE_REGEX = re.compile(r'phone:\s*"([^"]+)"')


def _extract_frontend_phones() -> set[str]:
    """Извлечь все номера из frontend/lib/crisis-contacts.ts."""
    assert FRONTEND_FILE.exists(), f"Файл {FRONTEND_FILE} не найден"
    content = FRONTEND_FILE.read_text(encoding="utf-8")
    return set(PHONE_REGEX.findall(content))


def _extract_backend_phones() -> set[str]:
    """Извлечь все номера из contacts.py (через импорт констант)."""
    phones: set[str] = set()
    for group in (
        UNIVERSAL_CONTACTS,
        CHILD_CONTACTS,
        YOUTH_CONTACTS,
        ADULT_CONTACTS,
        MOSCOW_CONTACTS,
    ):
        for contact in group:
            phones.add(contact.phone)
    return phones


def test_frontend_and_backend_phones_match():
    """Множества телефонов на frontend и backend должны совпадать."""
    frontend = _extract_frontend_phones()
    backend = _extract_backend_phones()

    missing_on_frontend = backend - frontend
    extra_on_frontend = frontend - backend

    assert not missing_on_frontend, (
        f"На frontend нет номеров: {missing_on_frontend}. "
        f"Добавь их в frontend/lib/crisis-contacts.ts."
    )
    assert not extra_on_frontend, (
        f"На frontend есть лишние номера: {extra_on_frontend}. "
        f"Удали их из frontend/lib/crisis-contacts.ts или добавь в contacts.py."
    )


def test_frontend_file_exists():
    """Sanity-check: файл существует и не пустой."""
    assert FRONTEND_FILE.exists()
    assert FRONTEND_FILE.stat().st_size > 100, "Файл подозрительно маленький"
