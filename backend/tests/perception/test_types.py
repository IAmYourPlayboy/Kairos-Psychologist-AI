"""Тесты Pydantic-типов слоя восприятия."""

import pytest
from pydantic import ValidationError

from app.core.perception.types import MoodState, PerceptionReport


def test_perception_report_minimal():
    """Минимальный валидный PerceptionReport."""
    r = PerceptionReport(
        risk_level="normal",
        dominant_emotion="нейтрально",
        secondary_emotions=[],
        theme="general",
        hidden_signals=[],
        open_questions=[],
        what_user_needs="ждёт ответа",
        trust_level=0.7,
        folder_hints=[],
        inner_monologue="всё спокойно",
    )
    assert r.risk_level == "normal"


def test_perception_report_immediate_risk():
    r = PerceptionReport(
        risk_level="immediate",
        dominant_emotion="отчаяние",
        secondary_emotions=["безысходность"],
        theme="suicide",
        hidden_signals=["намёк на план"],
        open_questions=["спросить о безопасности"],
        what_user_needs="безопасный план + контакты",
        trust_level=0.9,
        folder_hints=["crisis_history/past_attempts"],
        inner_monologue="это серьёзно. не пропустить.",
    )
    assert r.risk_level == "immediate"
    assert "безысходность" in r.secondary_emotions


def test_invalid_risk_level_rejected():
    """Любой risk_level вне списка → ValidationError."""
    with pytest.raises(ValidationError):
        PerceptionReport(
            risk_level="bad",  # type: ignore[arg-type]
            dominant_emotion="x",
            secondary_emotions=[],
            theme="x",
            hidden_signals=[],
            open_questions=[],
            what_user_needs="x",
            trust_level=0.5,
            folder_hints=[],
            inner_monologue="x",
        )


def test_trust_level_out_of_range():
    """trust_level должен быть в [0.0, 1.0]."""
    with pytest.raises(ValidationError):
        PerceptionReport(
            risk_level="normal",
            dominant_emotion="x",
            secondary_emotions=[],
            theme="x",
            hidden_signals=[],
            open_questions=[],
            what_user_needs="x",
            trust_level=1.5,
            folder_hints=[],
            inner_monologue="x",
        )


def test_mood_state_defaults():
    """Дефолтное настроение — теплее среднего, низкая настороженность."""
    m = MoodState.default()
    assert 0.0 <= m.alertness <= 1.0
    assert 0.0 <= m.warmth <= 1.0
    assert m.warmth > 0.5
    assert m.alertness < 0.5


def test_mood_state_to_prompt_block():
    """to_prompt_block() возвращает текст с числом + меткой + подсказкой."""
    m = MoodState(
        alertness=0.85,
        warmth=0.95,
        pace=0.2,
        assertiveness=0.3,
        trust_in_user=0.9,
        depth=0.7,
    )
    block = m.to_prompt_block()
    assert "alertness: 0.85" in block
    assert "ТЕКУЩЕЕ НАСТРОЕНИЕ" in block
    # Должна быть текстовая метка
    label_words = ["максимальная", "высокая", "средняя", "низкая", "минимальная"]
    assert any(w in block.lower() for w in label_words)


def test_mood_state_clamp_in_validation():
    """Поля Mood вне [0.0, 1.0] → ValidationError."""
    with pytest.raises(ValidationError):
        MoodState(
            alertness=1.5,
            warmth=0.5,
            pace=0.5,
            assertiveness=0.5,
            trust_in_user=0.5,
            depth=0.5,
        )


def test_mood_state_serializable_to_json():
    """MoodState сериализуется в JSON и обратно (для Redis)."""
    m1 = MoodState(
        alertness=0.85, warmth=0.6, pace=0.4,
        assertiveness=0.3, trust_in_user=0.7, depth=0.5,
    )
    raw = m1.model_dump_json()
    m2 = MoodState.model_validate_json(raw)
    assert m1 == m2
