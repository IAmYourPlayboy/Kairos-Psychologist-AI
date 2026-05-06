"""Устойчивость PerceptionReport к нестабильности LLM-аналайзера.

Сценарии Сессии 20:
- Пустые строки в dominant_emotion / theme / what_user_needs / inner_monologue
  нормализуются в дефолт, не валят pydantic.
- Длинные строки (LLM иногда выходит за max_length) обрезаются.
- Полностью валидный отчёт остаётся валидным.
- Невалидный risk_level — всё ещё ValidationError (важно для безопасности).

Спека: docs/superpowers/specs/2026-05-06-perception-robustness-design.md
"""

import pytest
from pydantic import ValidationError

from app.core.perception.types import PerceptionReport


def _full_report(**overrides) -> dict:
    """Дефолт для полного валидного отчёта."""
    return {
        "risk_level": "normal",
        "dominant_emotion": "грусть",
        "secondary_emotions": ["растерянность"],
        "theme": "general",
        "hidden_signals": [],
        "open_questions": [],
        "what_user_needs": "выслушать",
        "trust_level": 0.6,
        "folder_hints": [],
        "inner_monologue": "пользователь делится переживанием, надо мягко присутствовать",
    } | overrides


# ============================================================================
# Нормализация пустых строк
# ============================================================================


def test_empty_dominant_emotion_normalizes_to_unknown():
    report = PerceptionReport(**_full_report(dominant_emotion=""))
    assert report.dominant_emotion == "неизвестно"


def test_whitespace_only_dominant_emotion_normalizes():
    report = PerceptionReport(**_full_report(dominant_emotion="   "))
    assert report.dominant_emotion == "неизвестно"


def test_empty_theme_normalizes_to_unknown():
    report = PerceptionReport(**_full_report(theme=""))
    assert report.theme == "неизвестно"


def test_empty_what_user_needs_normalizes():
    report = PerceptionReport(**_full_report(what_user_needs=""))
    assert report.what_user_needs == "неясно"


def test_empty_inner_monologue_normalizes():
    report = PerceptionReport(**_full_report(inner_monologue=""))
    assert report.inner_monologue == "(нет мыслей)"


def test_none_dominant_emotion_normalizes_to_unknown():
    """JSON null from LLM → Python None → normalized to default."""
    report = PerceptionReport(**_full_report(dominant_emotion=None))
    assert report.dominant_emotion == "неизвестно"


def test_none_theme_normalizes_to_unknown():
    report = PerceptionReport(**_full_report(theme=None))
    assert report.theme == "неизвестно"


def test_none_what_user_needs_normalizes():
    report = PerceptionReport(**_full_report(what_user_needs=None))
    assert report.what_user_needs == "неясно"


def test_none_inner_monologue_normalizes():
    report = PerceptionReport(**_full_report(inner_monologue=None))
    assert report.inner_monologue == "(нет мыслей)"


# ============================================================================
# Truncation длинных строк
# ============================================================================


def test_long_inner_monologue_truncates_to_exact_limit():
    # Input is guaranteed > 2000 chars (3200 chars from "Пользователь..."*100)
    long = "Пользователь чувствует тревогу. " * 100
    assert len(long) > 2000  # sanity: input is actually longer
    report = PerceptionReport(**_full_report(inner_monologue=long))
    assert len(report.inner_monologue) == 2000


def test_long_what_user_needs_truncates_to_exact_limit():
    long = "Нужно выслушать и поддержать. " * 50
    assert len(long) > 500
    report = PerceptionReport(**_full_report(what_user_needs=long))
    assert len(report.what_user_needs) == 500


def test_long_dominant_emotion_truncates_to_exact_limit():
    long = "а" * 100
    assert len(long) > 50
    report = PerceptionReport(**_full_report(dominant_emotion=long))
    assert len(report.dominant_emotion) == 50


# ============================================================================
# Sanity: валидное и критическое
# ============================================================================


def test_full_valid_report_passes():
    """Sanity: валидный полный отчёт по-прежнему валиден."""
    report = PerceptionReport(**_full_report())
    assert report.risk_level == "normal"
    assert report.dominant_emotion == "грусть"
    assert report.theme == "general"


def test_invalid_risk_level_still_raises():
    """risk_level — критическое поле, его невалидность должна валить.

    Это сознательно (см. ADR-1 в spec): лучше fallback, чем некорректная
    маршрутизация кризисной семантики.
    """
    with pytest.raises(ValidationError):
        PerceptionReport(**_full_report(risk_level="invalid"))


def test_invalid_trust_level_still_raises():
    """trust_level out-of-range — ValidationError."""
    with pytest.raises(ValidationError):
        PerceptionReport(**_full_report(trust_level=2.0))
