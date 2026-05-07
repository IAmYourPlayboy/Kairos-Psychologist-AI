"""Тесты PromptBuilder — сборки финального промпта для основной LLM."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.perception.prompt_builder import (
    _pick_technique_digest,
    build_main_prompt,
)
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


# ============================================================================
# Тесты _pick_technique_digest и подмешивания техник (Сессия 23, Фаза 1.3).
# Спека: docs/superpowers/specs/2026-05-07-prompt-engineering-from-knowledge.md
# ============================================================================


def _custom_report(
    *,
    risk_level: str = "normal",
    dominant_emotion: str = "neutral",
    theme: str = "general",
) -> PerceptionReport:
    """Минимальный отчёт под конкретное правило выбора техники."""
    return PerceptionReport(
        risk_level=risk_level,
        dominant_emotion=dominant_emotion,
        secondary_emotions=[],
        theme=theme,
        hidden_signals=[],
        open_questions=[],
        what_user_needs="неясно",
        trust_level=0.5,
        folder_hints=[],
        inner_monologue="(нет мыслей)",
    )


def test_pick_technique_immediate_returns_none():
    """ADR-4: при immediate техники не подмешиваются (CRISIS_PROMPTS уже жёсткий)."""
    r = _custom_report(risk_level="immediate", dominant_emotion="безысходность")
    assert _pick_technique_digest(r) is None


def test_pick_technique_high_returns_validation():
    """High → всегда валидация перед предложением контактов."""
    r = _custom_report(risk_level="high")
    digest = _pick_technique_digest(r)
    assert digest is not None
    assert "ВАЛИДАЦИЯ" in digest


def test_pick_technique_elevated_with_fear_returns_grounding():
    """Elevated + страх/паника → заземление (ВОЗ PFA)."""
    r = _custom_report(risk_level="elevated", dominant_emotion="страх")
    digest = _pick_technique_digest(r)
    assert digest is not None
    assert "ЗАЗЕМЛЕНИЕ" in digest


def test_pick_technique_grief_theme_returns_act():
    """Тема горя/утраты → ACT."""
    r = _custom_report(theme="family/grandfather/смерть")
    digest = _pick_technique_digest(r)
    assert digest is not None
    assert "ACT" in digest


def test_pick_technique_family_conflict_returns_six_cs():
    """Тема семьи/конфликта/безысходности → SIX C's (мобилизация)."""
    r = _custom_report(theme="family/parents/конфликт")
    digest = _pick_technique_digest(r)
    assert digest is not None
    assert "SIX" in digest


def test_pick_technique_anger_emotion_returns_dbt():
    """Эмоция гнев → DBT."""
    r = _custom_report(dominant_emotion="гнев", theme="work")
    digest = _pick_technique_digest(r)
    assert digest is not None
    assert "DBT" in digest


def test_pick_technique_anxiety_theme_returns_cbt():
    """Тема тревоги без кризиса → CBT (когнитивные искажения)."""
    r = _custom_report(theme="тревога/exam", dominant_emotion="беспокойство")
    digest = _pick_technique_digest(r)
    assert digest is not None
    assert "CBT" in digest


def test_pick_technique_neutral_returns_none():
    """Если ни одно правило не подошло — None (минимизируем шум в промпте)."""
    r = _custom_report(theme="general", dominant_emotion="neutral")
    assert _pick_technique_digest(r) is None


def test_build_main_prompt_includes_technique_when_matched():
    """build_main_prompt подмешивает выжимку техники когда правило сработало."""
    r = _custom_report(
        risk_level="elevated",
        dominant_emotion="страх",
        theme="паника",
    )
    prompt = build_main_prompt(report=r, mood=MoodState.default(), relevant_facts=[])
    # Маркер из PFA_GROUNDING_DIGEST
    assert "ЗАЗЕМЛЕНИЕ" in prompt


def test_build_main_prompt_no_technique_when_no_rule_matches():
    """build_main_prompt не добавляет блок техники если ни одно правило не сработало."""
    r = _custom_report(theme="general", dominant_emotion="neutral")
    prompt = build_main_prompt(report=r, mood=MoodState.default(), relevant_facts=[])
    # Ни один маркер из выжимок не должен присутствовать
    technique_markers = [
        "ВАЛИДАЦИЯ ПЕРЕД ДЕЙСТВИЕМ",
        "ЗАЗЕМЛЕНИЕ (ВОЗ PFA",
        "SIX C's ФАРЧИ",
        "CBT ПРИ ТРЕВОГЕ",
        "DBT ПРИ ГНЕВЕ",
        "ACT ПРИ УТРАТЕ",
    ]
    for marker in technique_markers:
        assert marker not in prompt, f"Не должно быть маркера техники: {marker}"


def test_build_main_prompt_immediate_no_technique_added():
    """ADR-4: при immediate выжимка техники не подмешивается, остаётся только CRISIS_PROMPTS.

    NB: BASE_PROMPT уже упоминает «SIX C's Фарчи» в строке про протоколы, поэтому
    проверяем не сам этот текст, а заголовок выжимки техники (присутствует ТОЛЬКО
    в подмешиваемом блоке): «## ПОДХОД: SIX C's».
    """
    r = _custom_report(risk_level="immediate", theme="family/parents/конфликт")
    prompt = build_main_prompt(report=r, mood=MoodState.default(), relevant_facts=[])
    # Несмотря на тему семья/конфликт — выжимка SIX C's не подмешивается при immediate
    assert "## ПОДХОД: SIX C's" not in prompt
    # Но CRISIS_PROMPTS["immediate"] должен быть на месте
    assert "НЕМЕДЛЕННЫЙ" in prompt


def test_analyzer_prompt_includes_distress_levels_digest():
    """ANALYZER_SYSTEM_PROMPT после Сессии 23 содержит выжимку маркеров уровней."""
    from app.core.perception.analyzer_prompt import ANALYZER_SYSTEM_PROMPT
    # Маркер из WHO_PFA_DISTRESS_LEVELS
    assert "ВОЗ PFA" in ANALYZER_SYSTEM_PROMPT
    assert "CAPS LOCK" in ANALYZER_SYSTEM_PROMPT
    # Плейсхолдер должен быть подменён
    assert "{{WHO_PFA" not in ANALYZER_SYSTEM_PROMPT


def test_reflection_extract_prompt_includes_trigger_digests():
    """EXTRACT_SYSTEM_PROMPT после Сессии 23 содержит критерии триггеров."""
    from app.core.perception.reflection_prompt import EXTRACT_SYSTEM_PROMPT
    # Маркеры из CBT_TRIGGERS и DBT_TRIGGERS
    assert "КОГНИТИВНЫЙ ТРИГГЕР" in EXTRACT_SYSTEM_PROMPT
    assert "ЭМОЦИОНАЛЬНЫЙ ТРИГГЕР" in EXTRACT_SYSTEM_PROMPT
    # Плейсхолдеры должны быть подменены
    assert "{{CBT" not in EXTRACT_SYSTEM_PROMPT
    assert "{{DBT" not in EXTRACT_SYSTEM_PROMPT
