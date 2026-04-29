"""Кризисные контакты России по возрастным группам."""

from pydantic import BaseModel


class CrisisContact(BaseModel):
    """Один кризисный контакт."""

    name: str
    phone: str
    description: str


# Универсальные контакты (для всех возрастов)
UNIVERSAL_CONTACTS: list[CrisisContact] = [
    CrisisContact(
        name="Экстренные службы",
        phone="112",
        description="Единый номер экстренных служб (работает без SIM-карты)",
    ),
    CrisisContact(
        name="МЧС — психологическая помощь",
        phone="8-800-333-44-34",
        description="Бесплатно, круглосуточно, анонимно",
    ),
]

# Контакты для детей и подростков (до 18 лет)
CHILD_CONTACTS: list[CrisisContact] = [
    CrisisContact(
        name="Детский телефон доверия",
        phone="8-800-2000-122",
        description="Бесплатно, круглосуточно, анонимно (до 18 лет)",
    ),
]

# Контакты для молодёжи (до 25 лет)
YOUTH_CONTACTS: list[CrisisContact] = [
    CrisisContact(
        name="«Помощь рядом»",
        phone="8-800-100-49-94",
        description="Бесплатно, для молодёжи до 25 лет",
    ),
]

# Контакты для взрослых
ADULT_CONTACTS: list[CrisisContact] = [
    CrisisContact(
        name="Линия «0-24»",
        phone="8-800-700-84-60",
        description="Утрата, насилие, суицид — бесплатно, круглосуточно",
    ),
]

# Московские контакты
MOSCOW_CONTACTS: list[CrisisContact] = [
    CrisisContact(
        name="Московская служба психологической помощи",
        phone="051",
        description="С мобильного: 8-495-051",
    ),
]


def get_crisis_contacts(age_group: str | None = None) -> list[CrisisContact]:
    """Вернуть список кризисных контактов для возрастной группы.

    Args:
        age_group: "child" (до 18), "youth" (до 25), "adult" (25+) или None (все).

    Returns:
        Список контактов, начиная с универсальных.
    """
    contacts = list(UNIVERSAL_CONTACTS)

    if age_group == "child":
        contacts.extend(CHILD_CONTACTS)
        contacts.extend(YOUTH_CONTACTS)
    elif age_group == "youth":
        contacts.extend(YOUTH_CONTACTS)
        contacts.extend(ADULT_CONTACTS)
    elif age_group == "adult":
        contacts.extend(ADULT_CONTACTS)
    else:
        # Без указания возраста — все контакты
        contacts.extend(CHILD_CONTACTS)
        contacts.extend(YOUTH_CONTACTS)
        contacts.extend(ADULT_CONTACTS)

    return contacts
