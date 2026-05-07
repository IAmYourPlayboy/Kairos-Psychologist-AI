"""OpenAI-совместимый LLM-провайдер (Yandex AI Studio, vLLM, Cloud.ru)."""

import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

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
        extra_body: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """Отправить запрос и получить полный ответ.

        Args:
            extra_body: дополнительные поля для payload. Например, для
                Qwen 3.6 в Yandex AI Studio отключение reasoning mode:
                ``extra_body={"chat_template_kwargs": {"enable_thinking": False}}``
        """
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if extra_body:
            payload.update(extra_body)

        start = time.perf_counter()
        response = await self._client.post("/chat/completions", json=payload)
        elapsed_ms = (time.perf_counter() - start) * 1000

        response.raise_for_status()
        data = response.json()

        # content может быть None если модель не сгенерировала ответ
        # (например, reasoning_mode съел все max_tokens). Нормализуем в "".
        text = data["choices"][0]["message"].get("content") or ""

        raw_usage = data.get("usage", {})
        # Yandex возвращает cached_tokens во вложенной структуре prompt_tokens_details
        cached = (
            raw_usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)
            if isinstance(raw_usage.get("prompt_tokens_details"), dict)
            else 0
        )
        usage = UsageStats(
            prompt_tokens=raw_usage.get("prompt_tokens", 0),
            completion_tokens=raw_usage.get("completion_tokens", 0),
            total_tokens=raw_usage.get("total_tokens", 0),
            cached_tokens=cached,
        )

        logger.debug(
            "LLM ответ: %d токенов за %.0f мс (cached: %d)",
            usage.total_tokens, elapsed_ms, usage.cached_tokens,
        )

        return LLMResponse(text=text, usage=usage, response_time_ms=elapsed_ms)

    async def generate_stream(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        extra_body: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Отправить запрос и получить ответ потоково (SSE).

        Args:
            extra_body: см. ``generate``.
        """
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if extra_body:
            payload.update(extra_body)

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
