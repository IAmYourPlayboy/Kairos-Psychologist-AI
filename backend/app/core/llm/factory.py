"""Фабрика LLM-провайдеров: выбор реализации через переменные окружения."""

from app.config import settings
from app.core.llm.base import BaseLLMProvider
from app.core.llm.openai_compat import OpenAICompatProvider

# Все провайдеры, работающие через OpenAI-совместимый API
_OPENAI_COMPAT_PROVIDERS = {"yandex", "openai", "vllm", "cloudru"}

_provider: BaseLLMProvider | None = None


def get_provider() -> BaseLLMProvider:
    """Вернуть LLM-провайдер на основе настроек. Создаётся один раз (singleton).

    При settings.e2e_mode == True возвращает MockLLMProvider с
    детерминистичными ответами (для Playwright тестов).
    """
    global _provider
    if _provider is not None:
        return _provider

    if settings.e2e_mode:
        # E2E режим: mock с детерминистичными ответами по ключевым словам.
        # Используется ТОЛЬКО в Playwright тестах. В production не должен
        # активироваться никогда (флаг проброшен через ENV E2E_MODE=true).
        from app.core.llm.mock import MockLLMProvider
        _provider = MockLLMProvider()
        return _provider

    if settings.llm_provider in _OPENAI_COMPAT_PROVIDERS:
        _provider = OpenAICompatProvider(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
    else:
        raise ValueError(f"Неизвестный LLM-провайдер: {settings.llm_provider}")

    return _provider


def _reset_provider() -> None:
    """Сбросить singleton (только для тестов)."""
    global _provider
    _provider = None
