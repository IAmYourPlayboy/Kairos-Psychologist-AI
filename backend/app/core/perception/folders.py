"""Фиксированный список папок и подпапок досье.

Дизайн: §4.1 в spec.

Правила:
- 13 фиксированных верхнеуровневых папок + специальная "custom" для
  пользовательских папок (создаваемых ReflectionAgent).
- Подпапки для большинства папок фиксированы. Если папка их требует —
  подпапка не может быть NULL.
- Папки и подпапки именуются на английском snake_case.
- "custom" папка — особый случай: подпапка играет роль имени
  пользовательской категории (например custom/medical_visits).
"""

from __future__ import annotations


# Фиксированные папки верхнего уровня
TOP_LEVEL_FOLDERS: frozenset[str] = frozenset({
    "identity",        # как пользователь себя описывает (возраст, пол, статус)
    "childhood",       # события до 12-14 лет
    "family",          # родители, сиблинги, расширенная семья, дом
    "relationships",   # партнёры, дружба, школа (социальные связи)
    "work_school",     # учёба, работа, нагрузка
    "losses",          # утраты (смерти, расставания, переезды)
    "triggers",        # что ранит, болит, выбивает
    "resources",       # что помогает, кто рядом, на что опирается
    "values",          # что важно, во что верит
    "health",          # тело, сон, питание, болезни, внешность
    "crisis_history",  # прошлые кризисы, попытки, протоколы
    "goals",           # что хочет, к чему идёт
    "routines",        # ритуалы, режим (например "20:00 разговор")
    "custom",          # для пользовательских папок (см. ReflectionAgent)
})


# Допустимые подпапки. Пустой набор = подпапка опциональна (может быть None).
SUBFOLDERS: dict[str, frozenset[str]] = {
    "identity": frozenset(),  # подпапки не нужны
    "childhood": frozenset({"family", "school", "events"}),
    "family": frozenset({"parents", "siblings", "grandparents", "extended"}),
    "relationships": frozenset({"friends", "romantic", "school_peers", "colleagues"}),
    "work_school": frozenset({"current", "past", "performance"}),
    "losses": frozenset({"death", "breakup", "relocation", "other"}),
    "triggers": frozenset({"sensory", "situational", "relational"}),
    "resources": frozenset({"people", "activities", "skills", "places"}),
    "values": frozenset(),
    "health": frozenset({"body", "sleep", "illness", "appearance", "mental"}),
    "crisis_history": frozenset({"past_attempts", "past_episodes", "protective_factors"}),
    "goals": frozenset({"short_term", "long_term"}),
    "routines": frozenset({"daily", "weekly", "rituals"}),
    "custom": frozenset(),  # любое имя разрешено (snake_case)
}


# Папки, для которых подпапка ОБЯЗАТЕЛЬНА (без неё факт не записать).
REQUIRES_SUBFOLDER: frozenset[str] = frozenset({
    "family",
    "relationships",
    "triggers",
    "health",
    "custom",  # custom всегда требует имя пользовательской папки
})


def is_valid_folder(folder: str) -> bool:
    """Проверить, что folder из списка верхнего уровня."""
    return folder in TOP_LEVEL_FOLDERS


def is_valid_subfolder(folder: str, subfolder: str | None) -> bool:
    """Проверить, что (folder, subfolder) — допустимая пара.

    Логика:
    - "custom" — подпапка обязательна (это имя пользовательской папки),
      но может быть любой непустой строкой.
    - Если folder требует подпапку (REQUIRES_SUBFOLDER) — она должна быть
      из SUBFOLDERS[folder].
    - Если folder подпапку не требует — допустимо None или одна из
      SUBFOLDERS[folder].
    """
    if not is_valid_folder(folder):
        return False

    if folder == "custom":
        # custom требует non-empty имя, но любое (snake_case)
        return subfolder is not None and len(subfolder) > 0

    if folder in REQUIRES_SUBFOLDER:
        if subfolder is None:
            return False
        return subfolder in SUBFOLDERS[folder]

    # Подпапка опциональна
    if subfolder is None:
        return True
    return subfolder in SUBFOLDERS[folder]
