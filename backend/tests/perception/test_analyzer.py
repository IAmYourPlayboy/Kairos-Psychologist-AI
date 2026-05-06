"""Тесты MessageAnalyzer.

LLM замокан — мы тестируем парсинг JSON, валидацию, обработку ошибок.
"""

from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, patch

import pytest

# В тестах НЕ должно быть реальных вызовов LLM
os.environ["LLM_API_KEY"] = "test-key-not-real"
os.environ["LLM_MODEL"] = "test-model"

from app.core.llm.base import LLMResponse, UsageStats
from app.core.perception.analyzer import (
    AnalyzerError,
    MessageAnalyzer,
    strip_markdown_fence,
)
from app.core.perception.types import PerceptionReport


def _llm_response(text: str) -> LLMResponse:
    """Хелпер: создать заготовленный ответ LLM-провайдера."""
    return LLMResponse(
        text=text,
        usage=UsageStats(prompt_tokens=100, completion_tokens=50, total_tokens=150),
        response_time_ms=42.0,
    )


@pytest.fixture
def valid_json_text() -> str:
    return json.dumps(
        {
            "risk_level": "elevated",
            "dominant_emotion": "страх",
            "secondary_emotions": ["беспомощность"],
            "theme": "school_peers/bullying",
            "hidden_signals": ["возможно угроза не озвучена"],
            "open_questions": ["что именно сказали?"],
            "what_user_needs": "хочет, чтобы её услышали",
            "trust_level": 0.85,
            "folder_hints": ["relationships/school_peers"],
            "inner_monologue": "она вернулась к этой теме сама. не торопить.",
        },
        ensure_ascii=False,
    )


# ============================================================================
# strip_markdown_fence
# ============================================================================


def test_strip_no_fence_returns_as_is():
    assert strip_markdown_fence('{"a": 1}') == '{"a": 1}'


def test_strip_json_fence():
    assert strip_markdown_fence('```json\n{"a": 1}\n```') == '{"a": 1}'


def test_strip_plain_fence():
    assert strip_markdown_fence('```\n{"a": 1}\n```') == '{"a": 1}'


def test_strip_with_whitespace():
    assert strip_markdown_fence('   ```json\n{"a": 1}\n```  ') == '{"a": 1}'


# ============================================================================
# MessageAnalyzer.analyze
# ============================================================================


async def test_analyze_parses_valid_json(valid_json_text):
    """analyze() корректно парсит JSON-ответ LLM."""
    analyzer = MessageAnalyzer()
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm_response(valid_json_text)),
    ):
        report = await analyzer.analyze(
            current_message="опять туалет, страшно",
            history=[],
            dossier_summary="пусто",
        )

    assert isinstance(report, PerceptionReport)
    assert report.risk_level == "elevated"
    assert report.dominant_emotion == "страх"
    assert "relationships/school_peers" in report.folder_hints


async def test_analyze_strips_markdown_wrapper(valid_json_text):
    """LLM иногда оборачивает JSON в ```json ...```. Анализатор это снимает."""
    wrapped = f"```json\n{valid_json_text}\n```"
    analyzer = MessageAnalyzer()
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm_response(wrapped)),
    ):
        report = await analyzer.analyze(
            current_message="x",
            history=[],
            dossier_summary="пусто",
        )

    assert report.risk_level == "elevated"


async def test_analyze_invalid_json_raises():
    """Если LLM вернул не-JSON — AnalyzerError."""
    analyzer = MessageAnalyzer()
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm_response("это не json, а просто текст")),
    ):
        with pytest.raises(AnalyzerError, match="JSON"):
            await analyzer.analyze(
                current_message="x",
                history=[],
                dossier_summary="пусто",
            )


async def test_analyze_invalid_schema_raises():
    """Если JSON есть, но не соответствует схеме — AnalyzerError."""
    bad = json.dumps({"risk_level": "wrong_value", "dominant_emotion": "x"})
    analyzer = MessageAnalyzer()
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm_response(bad)),
    ):
        with pytest.raises(AnalyzerError):
            await analyzer.analyze(
                current_message="x",
                history=[],
                dossier_summary="пусто",
            )


async def test_analyze_llm_error_propagates():
    """Если LLM упал — исключение пробрасывается (НЕ глотаем).

    Это критическое решение из дизайн-спеки §9: rule-based fallback нет,
    при падении LLM честно сообщаем «извини, не могу».
    """
    analyzer = MessageAnalyzer()
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(side_effect=RuntimeError("LLM недоступен")),
    ):
        with pytest.raises(RuntimeError, match="LLM"):
            await analyzer.analyze(
                current_message="x",
                history=[],
                dossier_summary="пусто",
            )
