"""Тесты терапевтических промптов (Блок 3).

После Сессии 27 кризисный промпт собирается через `build_crisis_prompt(level, age_group)`,
а не через словарь `CRISIS_PROMPTS`. Тесты адаптированы под новый контракт.
"""

import pytest

from app.core.prompts.base import FORBIDDEN_PHRASES, PROMPT as BASE_PROMPT
from app.core.prompts.builder import build_system_prompt
from app.core.prompts.crisis import LEVELS, build_crisis_prompt


# --- Базовый промпт ---


def test_base_prompt_contains_role():
    assert "Кайрос" in BASE_PROMPT
    assert "не психолог" in BASE_PROMPT


def test_base_prompt_contains_forbidden_phrases_section():
    assert "ЗАПРЕЩЁННЫЕ ФРАЗЫ" in BASE_PROMPT


def test_forbidden_phrases_list_not_empty():
    assert len(FORBIDDEN_PHRASES) >= 7


# --- Ветка А: мобилизация ---


def test_branch_a_contains_mobilization():
    prompt = build_system_prompt("A", "normal")
    assert "МОБИЛИЗАЦИЯ" in prompt


def test_branch_a_contains_six_cs():
    prompt = build_system_prompt("A", "normal")
    assert "CHALLENGE" in prompt
    assert "CONTROL" in prompt
    assert "COMMITMENT" in prompt
    assert "CONTINUITY" in prompt
    assert "CALMNESS" in prompt


def test_branch_a_contains_shtab():
    prompt = build_system_prompt("A", "normal")
    assert "Штаб" in prompt


# --- Ветка Б: стабилизация ---


def test_branch_b_contains_stabilization():
    prompt = build_system_prompt("B", "normal")
    assert "СТАБИЛИЗАЦИЯ" in prompt


def test_branch_b_contains_grounding():
    prompt = build_system_prompt("B", "normal")
    assert "5-4-3-2-1" in prompt


def test_branch_b_contains_breathing():
    prompt = build_system_prompt("B", "normal")
    assert "4-4-6" in prompt


def test_branch_b_contains_instructor():
    prompt = build_system_prompt("B", "normal")
    assert "Инструктор" in prompt


# --- Кризисные промпты ---


def test_crisis_immediate_contains_universal_contacts():
    """В immediate всегда присутствуют универсальные контакты: 112 и МЧС.

    Старый билдер (этот путь) вызывает `build_crisis_prompt(level, age_group=None)`,
    поэтому попадают ВСЕ контакты — включая детский, youth и adult.
    """
    prompt = build_system_prompt("A", "immediate")
    assert "112" in prompt
    assert "8-800-333-44-34" in prompt  # МЧС


def test_crisis_high_contains_protocol_markers():
    """В high промпт описывает протокол валидации (без конкретных фраз бота — Сессия 27)."""
    prompt = build_system_prompt("A", "high")
    # Протокол HIGH включает валидацию через уточняющий вопрос
    assert "Валидируй" in prompt or "валидируй" in prompt or "ВЫСОКИЙ" in prompt


def test_crisis_elevated_contains_empathy_protocol():
    prompt = build_system_prompt("B", "elevated")
    assert "ПОВЫШЕННЫЙ" in prompt or "эмпатию" in prompt.lower()


def test_normal_has_no_crisis_section():
    prompt = build_system_prompt("A", "normal")
    assert "КРИЗИСНЫЙ РЕЖИМ" not in prompt


# --- Сборщик ---


def test_builder_includes_base_and_branch():
    prompt = build_system_prompt("A", "normal")
    assert "ЗАПРЕЩЁННЫЕ ФРАЗЫ" in prompt  # из base
    assert "МОБИЛИЗАЦИЯ" in prompt  # из branch_a


def test_builder_includes_crisis_when_not_normal():
    prompt = build_system_prompt("B", "immediate")
    assert "СТАБИЛИЗАЦИЯ" in prompt  # из branch_b
    assert "НЕМЕДЛЕННЫЙ" in prompt  # из crisis


def test_builder_case_insensitive_branch():
    prompt_lower = build_system_prompt("a", "normal")
    prompt_upper = build_system_prompt("A", "normal")
    assert prompt_lower == prompt_upper


def test_builder_unknown_branch_raises():
    with pytest.raises(ValueError, match="Неизвестная ветка"):
        build_system_prompt("C", "normal")


# --- Контракт build_crisis_prompt (Сессия 27) ---


def test_levels_constant_covers_all():
    assert set(LEVELS) == {"normal", "elevated", "high", "immediate"}


def test_build_crisis_prompt_normal_returns_none():
    """На normal кризисный блок не нужен → None."""
    assert build_crisis_prompt("normal") is None
    assert build_crisis_prompt("normal", age_group="adult") is None


def test_build_crisis_prompt_all_crisis_levels_return_text():
    for level in ("elevated", "high", "immediate"):
        prompt = build_crisis_prompt(level)
        assert prompt is not None
        assert len(prompt) > 0


def test_build_crisis_prompt_unknown_level_returns_none():
    assert build_crisis_prompt("unknown") is None


def test_all_prompts_contain_forbidden_block():
    """Все варианты промптов содержат блок запрещённых фраз (через base)."""
    for branch in ("A", "B"):
        for level in ("normal", "elevated", "high", "immediate"):
            prompt = build_system_prompt(branch, level)
            assert "НИКОГДА не говоришь" in prompt, (
                f"Промпт branch={branch}, crisis={level} не содержит запрещённые фразы"
            )
