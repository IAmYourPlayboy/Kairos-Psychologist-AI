"""Тесты LLM-абстракции (Блок 2)."""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.core.llm.base import LLMResponse, Message, UsageStats
from app.core.llm.factory import _reset_provider, get_provider
from app.core.llm.openai_compat import OpenAICompatProvider


# --- Фикстуры ---


MOCK_OPENAI_RESPONSE = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "Привет! Чем могу помочь?"},
            "finish_reason": "stop",
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 8,
        "total_tokens": 18,
    },
}


@pytest.fixture(autouse=True)
def reset_singleton():
    """Сбрасываем singleton провайдера перед каждым тестом."""
    _reset_provider()
    yield
    _reset_provider()


# --- Тесты моделей данных ---


def test_message_model():
    msg = Message(role="user", content="привет")
    assert msg.role == "user"
    assert msg.content == "привет"


def test_usage_stats_defaults():
    usage = UsageStats()
    assert usage.prompt_tokens == 0
    assert usage.total_tokens == 0


def test_llm_response_model():
    resp = LLMResponse(
        text="ответ",
        usage=UsageStats(prompt_tokens=5, completion_tokens=3, total_tokens=8),
        response_time_ms=42.0,
    )
    assert resp.text == "ответ"
    assert resp.usage.total_tokens == 8
    assert resp.response_time_ms == 42.0


# --- Тесты OpenAICompatProvider ---


@pytest.fixture
def provider():
    return OpenAICompatProvider(
        base_url="https://api.example.com/v1",
        api_key="test-key",
        model="test-model",
    )


@pytest.fixture
def yandex_provider():
    return OpenAICompatProvider(
        base_url="https://llm.api.cloud.yandex.net/foundationModels/v1",
        api_key="test-yandex-key",
        model="yandexgpt-lite",
    )


async def test_generate_returns_llm_response(provider: OpenAICompatProvider):
    """generate() корректно парсит OpenAI-совместимый ответ."""
    mock_response = httpx.Response(
        status_code=200,
        json=MOCK_OPENAI_RESPONSE,
        request=httpx.Request("POST", "https://api.example.com/v1/chat/completions"),
    )

    with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await provider.generate([Message(role="user", content="привет")])

    assert isinstance(result, LLMResponse)
    assert result.text == "Привет! Чем могу помочь?"
    assert result.usage.prompt_tokens == 10
    assert result.usage.completion_tokens == 8
    assert result.usage.total_tokens == 18
    assert result.response_time_ms > 0


async def test_generate_sends_correct_payload(provider: OpenAICompatProvider):
    """generate() отправляет правильный JSON в запросе."""
    mock_response = httpx.Response(
        status_code=200,
        json=MOCK_OPENAI_RESPONSE,
        request=httpx.Request("POST", "https://api.example.com/v1/chat/completions"),
    )

    with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        await provider.generate(
            [Message(role="user", content="тест")],
            temperature=0.5,
            max_tokens=512,
        )

    call_kwargs = mock_post.call_args
    payload = call_kwargs.kwargs["json"]
    assert payload["model"] == "test-model"
    assert payload["temperature"] == 0.5
    assert payload["max_tokens"] == 512
    assert payload["stream"] is False
    assert payload["messages"] == [{"role": "user", "content": "тест"}]


async def test_bearer_auth_for_generic_provider(provider: OpenAICompatProvider):
    """Обычные провайдеры используют Bearer-авторизацию."""
    auth = provider._client.headers["authorization"]
    assert auth == "Bearer test-key"


async def test_api_key_auth_for_yandex(yandex_provider: OpenAICompatProvider):
    """Yandex AI Studio использует Api-Key авторизацию."""
    auth = yandex_provider._client.headers["authorization"]
    assert auth == "Api-Key test-yandex-key"


async def test_close(provider: OpenAICompatProvider):
    """close() закрывает httpx-клиент."""
    await provider.close()
    assert provider._client.is_closed


# --- Тесты фабрики ---


def test_get_provider_returns_openai_compat():
    """get_provider() создаёт OpenAICompatProvider для yandex."""
    provider = get_provider()
    assert isinstance(provider, OpenAICompatProvider)


def test_get_provider_singleton():
    """get_provider() возвращает один и тот же экземпляр."""
    p1 = get_provider()
    p2 = get_provider()
    assert p1 is p2


def test_get_provider_unknown_raises():
    """get_provider() бросает ValueError для неизвестного провайдера."""
    with patch("app.core.llm.factory.settings") as mock_settings:
        mock_settings.llm_provider = "unknown_provider"
        with pytest.raises(ValueError, match="Неизвестный LLM-провайдер"):
            get_provider()
