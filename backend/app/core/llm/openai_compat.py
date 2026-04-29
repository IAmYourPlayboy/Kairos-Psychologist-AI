"""OpenAI-совместимый LLM-провайдер (Yandex AI Studio, vLLM, Cloud.ru)."""

import json
import logging
import time
from collections.abc import AsyncIterator

import httpx

from app.core.llm.base import BaseLLMProvider, LLMResponse, Message, UsageStats

logger = logging.getLogger(__name__)


class OpenAICompatProvider(BaseLLMProvider):
    """Провайдер для любого API, совместимого с OpenAI Chat Completions.

    Поддерживает Yandex Cloud AI Studio, self-hosted vLLM, Cloud.ru
    и любой другой сервис с эндпоинтом /chat/completions.
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 30.0,
    ) -> None:
        self._model = model

        # Yandex AI Studio использует «Api-Key», остальные — «Bearer»
        if "yandex" in base_url.lower():
            auth_value = f"Api-Key {api_key}"
        else:
            auth_value = f"Bearer {api_key}"

        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={
                "Authorization": auth_value,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def generate(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Отправить запрос и получить полный ответ."""
        payload = {
            "model": self._model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        start = time.perf_counter()
        response = await self._client.post("/chat/completions", json=payload)
        elapsed_ms = (time.perf_counter() - start) * 1000

        response.raise_for_status()
        data = response.json()

        text = data["choices"][0]["message"]["content"]
        raw_usage = data.get("usage", {})
        usage = UsageStats(
            prompt_tokens=raw_usage.get("prompt_tokens", 0),
            completion_tokens=raw_usage.get("completion_tokens", 0),
            total_tokens=raw_usage.get("total_tokens", 0),
        )

        logger.debug(
            "LLM ответ: %d токенов за %.0f мс", usage.total_tokens, elapsed_ms
        )

        return LLMResponse(text=text, usage=usage, response_time_ms=elapsed_ms)

    async def generate_stream(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """Отправить запрос и получить ответ потоково (SSE)."""
        payload = {
            "model": self._model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with self._client.stream(
            "POST", "/chat/completions", json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[len("data: ") :]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content")
                if content:
                    yield content

    async def close(self) -> None:
        """Закрыть HTTP-клиент."""
        await self._client.aclose()
