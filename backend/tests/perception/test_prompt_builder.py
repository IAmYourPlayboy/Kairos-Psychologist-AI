"""Тесты PromptBuilder — сборки финального промпта для основной LLM."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.perception.prompt_builder import build_main_prompt
from app.core.perception.types import MoodState, PerceptionReport
from app.data.dossier_models import DossierFact


def _report(risk: str = "normal") -> PerceptionReport:
    return PerceptionReport(
        risk_level=risk,
        dominant_emotion="страх",
        secondary_emotions=["беспомощность"],
        theme="school_peers/bullying",
        hidden_signals=["возможно угрозу не озвучила"],
        open_questions=["что именно сказали"],
        what_user_needs="хочет, чтобы её услышали",
        trust_level=0.85,
        folder_hints=["relationships/school_peers"],
        inner_monologue="не торопить. она вернулась к этой теме.",
    )


def _mood() -> MoodState:
    return MoodState(
        alertness=0.8, warmth=0.95, pace=0.25,
        assertiveness=0.3, trust_in_user=0.85, depth=0.6,
    )


def _fact() -> DossierFact:
    f = DossierFact(
        id="f-1", user_id="u-1",
        folder="relationships", subfolder="school_peers",
        summary="Мальчики в классе угрожают",
        tags=["threat"],
        severity=0.9, confidence=0.85,
        first_mentioned=datetime.now(timezone.utc),
        last_mentioned=datetime.now(timezone.utc),
        times_mentioned=3,
        source_session_ids=[], source_message_ids=[],
        superseded_by=None,
    )
    f.quotes = []
    return f


def test_prompt_includes_mood_block():
    prompt = build_main_prompt(
        report=_report("elevated"),
        mood=_mood(),
        relevant_facts=[],
    )
    assert "ТЕКУЩЕЕ НАСТРОЕНИЕ" in prompt
    assert "alertness: 0.80" in prompt


def test_prompt_includes_dossier_when_facts_present():
    prompt = build_main_prompt(
        report=_report(),
        mood=_mood(),
        relevant_facts=[_fact()],
    )
    assert "ЧТО Я ЗНАЮ" in prompt
    assert "Мальчики в классе угрожают" in prompt


def test_prompt_excludes_dossier_block_when_empty():
    prompt = build_main_prompt(
        report=_report(),
        mood=_mood(),
        relevant_facts=[],
    )
    assert "ЧТО Я ЗНАЮ" not in prompt


def test_prompt_includes_inner_monologue_marked_internal():
    prompt = build_main_prompt(
        report=_report(),
        mood=_mood(),
        relevant_facts=[],
    )
    assert "не торопить" in prompt
    # Должна быть пометка что это внутренние мысли (не озвучивать)
    assert "ВНУТРЕННИЕ МЫСЛИ" in prompt or "ТВОИ МЫСЛИ" in prompt
    assert "НЕ озвучивать" in prompt or "НЕ показывать" in prompt


def test_prompt_includes_what_user_needs():
    prompt = build_main_prompt(
        report=_report(),
        mood=_mood(),
        relevant_facts=[],
    )
    assert "хочет, чтобы её услышали" in prompt
    assert "ЧТО НУЖНО ПОЛЬЗОВАТЕЛЮ" in prompt


def test_prompt_includes_base_kairos_prompt():
    """Базовый промпт Кайроса (роль, запреты) должен быть в финальном."""
    prompt = build_main_prompt(
        report=_report(),
        mood=_mood(),
        relevant_facts=[],
    )
    assert "Кайрос" in prompt
    assert "ЗАПРЕЩЁННЫЕ ФРАЗЫ" in prompt


def test_prompt_immediate_risk_includes_crisis_section():
    """При immediate риске должен быть кризисный блок (с контактами)."""
    prompt = build_main_prompt(
        report=_report("immediate"),
        mood=_mood(),
        relevant_facts=[],
    )
    # Кризисный блок содержит экстренные контакты
    assert "112" in prompt or "8-800" in prompt


def test_prompt_normal_risk_no_crisis_section():
    """При normal риске кризисный блок не добавляется."""
    prompt = build_main_prompt(
        report=_report("normal"),
        mood=_mood(),
        relevant_facts=[],
    )
    # При normal — нет кризисного блока (см. CRISIS_PROMPTS — для normal None)
    # Поэтому проверяем что нет специфичного кризисного маркера
    assert "НЕМЕДЛЕННЫЙ" not in prompt
