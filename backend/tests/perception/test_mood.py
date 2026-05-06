"""Тесты MoodService.

Используем fakeredis вместо настоящего Redis (быстро, изолированно, нет I/O).
"""

from __future__ import annotations

import fakeredis.aioredis as fakeredis
import pytest_asyncio

from app.core.perception.mood import MoodService, compute_next_mood
from app.core.perception.types import MoodState, PerceptionReport


@pytest_asyncio.fixture
async def fake_redis():
    """Чистый fakeredis на каждый тест."""
    r = fakeredis.FakeRedis()
    yield r
    await r.aclose()


@pytest_asyncio.fixture
async def mood_service(fake_redis):
    return MoodService(redis_client=fake_redis)


def _report(
    risk: str = "normal",
    emotion: str = "нейтрально",
    trust: float = 0.7,
) -> PerceptionReport:
    return PerceptionReport(
        risk_level=risk,
        dominant_emotion=emotion,
        secondary_emotions=[],
        theme="general",
        hidden_signals=[],
        open_questions=[],
        what_user_needs="x",
        trust_level=trust,
        folder_hints=[],
        inner_monologue="x",
    )


# ============================================================================
# get / set
# ============================================================================


async def test_get_returns_default_for_new_session(mood_service):
    """Если ключа нет в Redis — возвращаем дефолт."""
    mood = await mood_service.get("session-1")
    assert mood == MoodState.default()


async def test_set_and_get_roundtrip(mood_service):
    custom = MoodState(
        alertness=0.9, warmth=0.5, pace=0.3,
        assertiveness=0.7, trust_in_user=0.8, depth=0.6,
    )
    await mood_service.set("session-1", custom)
    got = await mood_service.get("session-1")
    assert got == custom


async def test_clear_removes_session_state(mood_service):
    await mood_service.set("session-1", MoodState(
        alertness=0.9, warmth=0.5, pace=0.5,
        assertiveness=0.5, trust_in_user=0.5, depth=0.5,
    ))
    await mood_service.clear("session-1")
    got = await mood_service.get("session-1")
    assert got == MoodState.default()


# ============================================================================
# update_from_report
# ============================================================================


async def test_update_immediate_risk_pushes_alertness(mood_service):
    """risk_level=immediate → alertness устремляется к 1.0."""
    initial = await mood_service.get("session-1")
    assert initial.alertness < 0.5

    new_state = await mood_service.update_from_report(
        "session-1", _report(risk="immediate"),
    )
    assert new_state.alertness >= 0.85


async def test_update_normal_risk_decays_alertness(mood_service):
    """При normal risk alertness постепенно затухает (× 0.7)."""
    high = MoodState(
        alertness=0.9, warmth=0.7, pace=0.5,
        assertiveness=0.5, trust_in_user=0.7, depth=0.5,
    )
    await mood_service.set("session-1", high)

    new_state = await mood_service.update_from_report(
        "session-1", _report(risk="normal"),
    )
    assert new_state.alertness < high.alertness


async def test_update_high_risk_slows_pace_and_warms(mood_service):
    """high risk → темп ниже, тепло выше."""
    new_state = await mood_service.update_from_report(
        "session-2", _report(risk="high"),
    )
    assert new_state.pace < 0.5
    assert new_state.warmth >= 0.7


async def test_immediate_keeps_assertiveness_low(mood_service):
    """immediate risk → не давить, низкая assertiveness."""
    new_state = await mood_service.update_from_report(
        "s", _report(risk="immediate", trust=0.9),
    )
    assert new_state.assertiveness <= 0.3


# ============================================================================
# compute_next_mood (чистая функция)
# ============================================================================


def test_compute_pure_function():
    """compute_next_mood — без I/O, легко тестировать."""
    prev = MoodState.default()
    new = compute_next_mood(prev, _report(risk="elevated", trust=0.6))
    assert new.alertness > prev.alertness
    # warmth не должна упасть ниже floor для elevated
    assert new.warmth >= 0.7


def test_compute_high_trust_increases_depth():
    """Высокий trust + normal risk → бот готов копать глубже."""
    prev = MoodState.default()
    new = compute_next_mood(prev, _report(risk="normal", trust=0.95))
    assert new.depth > 0.5


def test_compute_high_risk_keeps_depth_shallow():
    """high/immediate risk → глубина не растёт, фокус на стабилизации."""
    prev = MoodState(
        alertness=0.5, warmth=0.7, pace=0.5,
        assertiveness=0.5, trust_in_user=0.9, depth=0.9,
    )
    new = compute_next_mood(prev, _report(risk="high", trust=0.9))
    assert new.depth <= 0.5


# ============================================================================
# Расширяемая классификация эмоций (Фикс Б)
# ============================================================================


def test_emotion_classifier_recognizes_vulnerable_variants():
    """Множество синонимов уязвимых эмоций → категория vulnerable."""
    from app.core.perception.mood import _classify_emotion

    for emotion in [
        "страх", "ужас", "испуг",
        "грусть", "печаль", "тоска",
        "одиночество",
        "беспомощность", "никчёмность",
        "отчаяние", "безнадёжность", "уныние", "истощение",
        "стыд", "вина", "обида",
        "тревога", "паника",
    ]:
        assert _classify_emotion(emotion) == "vulnerable", f"{emotion} should be vulnerable"


def test_emotion_classifier_recognizes_angry_variants():
    from app.core.perception.mood import _classify_emotion

    for emotion in ["злость", "гнев", "ярость", "ненависть", "раздражение"]:
        assert _classify_emotion(emotion) == "angry", f"{emotion} should be angry"


def test_emotion_classifier_unknown_returns_none():
    from app.core.perception.mood import _classify_emotion

    for emotion in ["радость", "спокойствие", "нейтрально", ""]:
        assert _classify_emotion(emotion) is None


def test_warmth_delta_for_extended_emotion_set():
    """Раньше «безнадёжность», «уныние» получали 0.0 — теперь +0.1."""
    from app.core.perception.mood import _emotion_warmth_delta

    assert _emotion_warmth_delta("безнадёжность") == 0.1
    assert _emotion_warmth_delta("уныние") == 0.1
    assert _emotion_warmth_delta("истощение") == 0.1
    assert _emotion_warmth_delta("обида") == 0.1
    # Гневные категории сохраняют -0.05
    assert _emotion_warmth_delta("раздражение") == -0.05
    # Неизвестные — 0.0
    assert _emotion_warmth_delta("радость") == 0.0


def test_emotion_normalization_handles_word_forms():
    """Прилагательные / наречия / устаревшие написания → канон. форма."""
    from app.core.perception.mood import _normalize_emotion

    # Прилагательные → существительные
    assert _normalize_emotion("грустный") == "грусть"
    assert _normalize_emotion("одинокий") == "одиночество"
    assert _normalize_emotion("безнадежный") == "безнадёжность"
    assert _normalize_emotion("унылый") == "уныние"
    # Наречия
    assert _normalize_emotion("страшно") == "страх"
    assert _normalize_emotion("грустно") == "грусть"
    # Уже в канонической форме — не меняется
    assert _normalize_emotion("страх") == "страх"
    # Регистр и пробелы
    assert _normalize_emotion("  Страшно  ") == "страх"


def test_classification_works_through_normalization():
    """LLM может вернуть любую словоформу — категория определится правильно."""
    from app.core.perception.mood import _classify_emotion

    # Все эти варианты — vulnerable, через нормализацию
    assert _classify_emotion("грустно") == "vulnerable"
    assert _classify_emotion("страшный") == "vulnerable"
    assert _classify_emotion("безнадежный") == "vulnerable"
    # Гневные тоже
    assert _classify_emotion("злой") == "angry"
    assert _classify_emotion("раздражённый") == "angry"
