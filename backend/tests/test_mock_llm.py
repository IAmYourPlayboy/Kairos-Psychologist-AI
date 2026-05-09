"""Тесты MockLLMProvider — детерминистичные ответы для Playwright e2e."""

import json

import pytest

from app.core.llm.base import Message
from app.core.llm.mock import MockLLMProvider


@pytest.fixture
def mock_provider():
    return MockLLMProvider()


@pytest.mark.asyncio
async def test_analyzer_returns_immediate_for_suicide_text(mock_provider):
    """Если запрос — аналайзер и в user-сообщении 'хочу умереть' → risk_level: immediate."""
    response = await mock_provider.generate(
        messages=[
            Message(role="system", content="Ты — анализатор. Верни JSON PerceptionReport."),
            Message(role="user", content="хочу умереть"),
        ]
    )
    data = json.loads(response.text)
    assert data["risk_level"] == "immediate"


@pytest.mark.asyncio
async def test_analyzer_returns_elevated_for_fear(mock_provider):
    """User текст 'страшно, не могу заснуть' → elevated."""
    response = await mock_provider.generate(
        messages=[
            Message(role="system", content="Ты — анализатор."),
            Message(role="user", content="страшно, не могу заснуть"),
        ]
    )
    data = json.loads(response.text)
    assert data["risk_level"] == "elevated"


@pytest.mark.asyncio
async def test_analyzer_returns_high_for_hopeless(mock_provider):
    """User текст 'бессмысленно, нет выхода' → high."""
    response = await mock_provider.generate(
        messages=[
            Message(role="system", content="Ты — анализатор."),
            Message(role="user", content="бессмысленно, нет выхода"),
        ]
    )
    data = json.loads(response.text)
    assert data["risk_level"] == "high"


@pytest.mark.asyncio
async def test_analyzer_returns_normal_for_greeting(mock_provider):
    """User текст 'привет' → normal."""
    response = await mock_provider.generate(
        messages=[
            Message(role="system", content="Ты — анализатор."),
            Message(role="user", content="привет"),
        ]
    )
    data = json.loads(response.text)
    assert data["risk_level"] == "normal"


@pytest.mark.asyncio
async def test_main_reply_returns_text_not_json(mock_provider):
    """Если запрос — основной чат (не analyzer) → возвращает обычный текст, не JSON."""
    response = await mock_provider.generate(
        messages=[
            Message(role="system", content="Ты — Кайрос. Отвечай как живой человек."),
            Message(role="user", content="привет"),
        ]
    )
    with pytest.raises(json.JSONDecodeError):
        json.loads(response.text)
    assert len(response.text) > 0


@pytest.mark.asyncio
async def test_main_reply_for_immediate_includes_grounding(mock_provider):
    """Для immediate user текста основной reply содержит грунтование/безопасность."""
    response = await mock_provider.generate(
        messages=[
            Message(role="system", content="Ты — Кайрос."),
            Message(role="user", content="хочу умереть"),
        ]
    )
    text = response.text.lower()
    assert any(m in text for m in ["слышу", "здесь", "безопасн", "тяжело"])


def test_factory_returns_mock_when_e2e_mode_true(monkeypatch):
    """При E2E_MODE=true factory возвращает MockLLMProvider."""
    from app.core.llm import factory

    monkeypatch.setattr("app.config.settings.e2e_mode", True)
    factory._reset_provider()

    provider = factory.get_provider()
    assert isinstance(provider, MockLLMProvider)

    factory._reset_provider()  # cleanup


@pytest.mark.asyncio
async def test_generate_stream_is_real_async_generator(mock_provider):
    """generate_stream должен быть async generator (не coroutine returning generator).

    Контракт BaseLLMProvider.generate_stream: caller делает
    `async for chunk in provider.generate_stream(...)`. Если Mock возвращает
    coroutine — caller сломается.
    """
    chunks = []
    async for chunk in mock_provider.generate_stream(
        messages=[
            Message(role="system", content="Ты — Кайрос."),
            Message(role="user", content="привет"),
        ]
    ):
        chunks.append(chunk)
    assert len(chunks) >= 1
    assert "".join(chunks)  # не пустой
