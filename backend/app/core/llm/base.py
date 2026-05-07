"""Базовый класс LLM-провайдера и модели данных."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel


class Message(BaseModel):
    """Сообщение в формате OpenAI Chat API."""

    role: str  # "system" | "user" | "assistant"
    content: str


class UsageStats(BaseModel):
    """Статистика использования токенов.

    cached_tokens — сколько входных токенов попало в кеш провайдера.
    Тарифицируются по сниженной ставке (например, у Qwen3.6 35B
    это 0.05₽/1К vs обычные 0.2₽/1К — экономия 75%).
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0


class LLMResponse(BaseModel):
    """Ответ от LLM-провайдера.

    text может быть пустой строкой если модель ничего не сгенерировала
    (например, при reasoning_mode исчерпала все токены на размышления).
    Провайдер должен нормализовать None → "" при возврате.
    """

    text: str
    usage: UsageStats = UsageStats()
    response_time_ms: float = 0.0


class BaseLLMProvider(ABC):
    """Абстрактный базовый класс для всех LLM-провайдеров.

    Любой провайдер (Yandex, vLLM, Cloud.ru) реализует этот интерфейс.
    Переключение между провайдерами — через переменную окружения LLM_PROVIDER.

    Параметр `extra_body`:
        Свободный словарь, прокидываемый в payload запроса как есть.
        Используется для специфичных полей конкретного провайдера, которых
        нет в стандартном OpenAI API. Например, для Qwen 3.6 в Yandex AI Studio
        отключение reasoning mode делается через:
            extra_body={"chat_template_kwargs": {"enable_thinking": False}}
        Если провайдер не поддерживает поле — он сам решает что делать
        (игнорировать или вернуть ошибку).
    """

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        extra_body: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """Сгенерировать ответ (полный, без стриминга)."""
        ...

    @abstractmethod
    def generate_stream(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        extra_body: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Сгенерировать ответ потоково (SSE-чанки текста)."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Закрыть HTTP-клиент и освободить ресурсы."""
        ...
