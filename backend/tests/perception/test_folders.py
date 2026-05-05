"""Тесты структуры папок досье (см. spec §4.1)."""

from app.core.perception.folders import (
    TOP_LEVEL_FOLDERS,
    SUBFOLDERS,
    is_valid_folder,
    is_valid_subfolder,
)


def test_thirteen_top_folders_plus_custom():
    """Верхний уровень = 13 фиксированных + custom."""
    assert "identity" in TOP_LEVEL_FOLDERS
    assert "family" in TOP_LEVEL_FOLDERS
    assert "custom" in TOP_LEVEL_FOLDERS
    assert len(TOP_LEVEL_FOLDERS) == 14


def test_subfolders_for_family():
    """family имеет правильные подпапки."""
    assert SUBFOLDERS["family"] == frozenset(
        {"parents", "siblings", "grandparents", "extended"}
    )


def test_subfolders_for_health():
    """health включает body, sleep, illness, appearance, mental."""
    assert "appearance" in SUBFOLDERS["health"]
    assert "mental" in SUBFOLDERS["health"]
    assert "body" in SUBFOLDERS["health"]


def test_is_valid_folder():
    """Только из TOP_LEVEL_FOLDERS считается валидным."""
    assert is_valid_folder("family") is True
    assert is_valid_folder("nonsense") is False
    # Custom-папки разрешены через "custom"
    assert is_valid_folder("custom") is True


def test_is_valid_subfolder_within_folder():
    """Подпапка проверяется на принадлежность списку SUBFOLDERS[folder]."""
    assert is_valid_subfolder("family", "parents") is True
    assert is_valid_subfolder("family", "wrong") is False
    # Папки без обязательных подпапок (например identity) разрешают None
    assert is_valid_subfolder("identity", None) is True


def test_subfolder_required_for_family():
    """family требует подпапку (нет валидного None)."""
    assert is_valid_subfolder("family", None) is False


def test_custom_folder_accepts_any_subfolder():
    """custom — special case, любая подпапка валидна.

    Это пользовательская папка, имя — английский snake_case.
    """
    assert is_valid_subfolder("custom", "medical_visits") is True
    # custom БЕЗ имени бессмысленна
    assert is_valid_subfolder("custom", None) is False
