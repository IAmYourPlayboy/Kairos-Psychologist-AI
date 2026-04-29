"""Тесты терапевтических промптов (Блок 3)."""

import pytest

from app.core.prompts.base import FORBIDDEN_PHRASES, PROMPT as BASE_PROMPT
from app.core.prompts.builder import build_system_prompt
from app.core.prompts.crisis import CRISIS_PROMPTS


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


def test_crisis_immediate_contains_contacts():
    prompt = build_system_prompt("A", "immediate")
    assert "8-800-2000-122" in prompt
    assert "112" in prompt


def test_crisis_high_contains_validation():
    prompt = build_system_prompt("A", "high")
    assert "Тебе сейчас очень тяжело" in prompt


def test_crisis_elevated_contains_empathy():
    prompt = build_system_prompt("B", "elevated")
    assert "дистресс" in prompt.lower() or "эмпатию" in prompt.lower()


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


def test_all_crisis_levels_exist():
    assert "elevated" in CRISIS_PROMPTS
    assert "high" in CRISIS_PROMPTS
    assert "immediate" in CRISIS_PROMPTS


def test_all_prompts_contain_forbidden_block():
    """Все варианты промптов содержат блок запрещённых фраз (через base)."""
    for branch in ("A", "B"):
        for level in ("normal", "elevated", "high", "immediate"):
            prompt = build_system_prompt(branch, level)
            assert "НИКОГДА не говоришь" in prompt, (
                f"Промпт branch={branch}, crisis={level} не содержит запрещённые фразы"
            )
