"""Базовый класс LLM-провайдера и модели данных."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from pydantic import BaseModel


class Message(BaseModel):
    """Сообщение в формате OpenAI Chat API."""

    role: str  # "system" | "user" | "assistant"
    content: str


class UsageStats(BaseModel):
    """Статистика использования токенов."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMResponse(BaseModel):
    """Ответ от LLM-провайдера."""

    text: str
    usage: UsageStats = UsageStats()
    response_time_ms: float = 0.0


class BaseLLMProvider(ABC):
    """Абстрактный базовый класс для всех LLM-провайдеров.

    Любой провайдер (Yandex, vLLM, Cloud.ru) реализует этот интерфейс.
    Переключение между провайдерами — через переменную окружения LLM_PROVIDER.
    """

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
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
    ) -> AsyncIterator[str]:
        """Сгенерировать ответ потоково (SSE-чанки текста)."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Закрыть HTTP-клиент и освободить ресурсы."""
        ...
