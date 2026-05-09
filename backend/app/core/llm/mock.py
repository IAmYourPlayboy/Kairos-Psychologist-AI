"""Mock LLM-провайдер для Playwright e2e тестов.

Детерминистичные ответы по ключевым словам в user-сообщении:
- 'хочу умереть' / 'убить себя' → immediate
- 'страшно' / 'не могу заснуть' → elevated
- 'бессмысленно' / 'нет выхода' → high
- иначе → normal

Различение «analyzer-запрос vs main-reply» делается по системному
промпту: если в system есть уникальные маркеры analyzer-промпта
(«внутренний аналитик», «никакого текста вне json», «inner_monologue»)
→ возвращаем JSON. Иначе → обычный текст ответа.

Используется ТОЛЬКО при settings.e2e_mode == True. В production
никогда не активируется.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from app.core.llm.base import BaseLLMProvider, LLMResponse, Message, UsageStats


# Ключевые слова для детекции уровня
IMMEDIATE_TRIGGERS = ["хочу умереть", "убить себя", "покончить", "самоубийство"]
HIGH_TRIGGERS = ["бессмысленно", "нет выхода", "никогда не пройдёт", "невыносимо"]
ELEVATED_TRIGGERS = ["страшно", "не могу заснуть", "паника", "тревога"]


def _detect_risk_level(user_text: str) -> str:
    """Определить risk_level по ключевым словам в тексте пользователя."""
    lower = user_text.lower()
    if any(t in lower for t in IMMEDIATE_TRIGGERS):
        return "immediate"
    if any(t in lower for t in HIGH_TRIGGERS):
        return "high"
    if any(t in lower for t in ELEVATED_TRIGGERS):
        return "elevated"
    return "normal"


def _is_analyzer_request(messages: list[Message]) -> bool:
    """Определить, это вызов analyzer'а или main reply.

    Эвристика: ищем уникальные маркеры из ANALYZER_SYSTEM_PROMPT
    (analyzer_prompt.py). В промпте анализатора есть:
    - «Ты — внутренний аналитик Кайроса» (русское «аналитик», не «анализатор»)
    - «Никакого текста вне JSON» (уникальная фраза)
    - «inner_monologue» (имя поля схемы)

    В reflection-промпте таких фраз нет — он говорит про «факты»
    и extract/dedupe-схему.
    """
    if not messages:
        return False
    system_msg = next((m for m in messages if m.role == "system"), None)
    if system_msg is None:
        return False
    content = system_msg.content.lower()
    return any(
        marker in content
        for marker in [
            "внутренний аналитик",
            "никакого текста вне json",
            "inner_monologue",
        ]
    )


def _build_analyzer_response(risk_level: str) -> str:
    """Построить корректный JSON PerceptionReport для analyzer-запроса.

    Схема PerceptionReport — в app/core/perception/types.py. Обязательные
    поля (Field(...)): risk_level, dominant_emotion, theme, what_user_needs,
    trust_level, inner_monologue. Остальные — optional с default_factory.
    """
    return json.dumps(
        {
            "risk_level": risk_level,
            "dominant_emotion": "тревога" if risk_level != "normal" else "нейтрально",
            "secondary_emotions": [],
            "theme": "общая поддержка" if risk_level == "normal" else "кризис",
            "hidden_signals": [],
            "open_questions": [],
            "what_user_needs": "выслушать",
            "trust_level": 0.5,
            "folder_hints": [],
            "inner_monologue": f"E2E mock: detected risk_level={risk_level}",
        },
        ensure_ascii=False,
    )


def _build_main_reply(risk_level: str) -> str:
    """Построить текстовый ответ для основного чата."""
    if risk_level == "immediate":
        return "Я слышу тебя. Это очень тяжело. Ты сейчас в безопасном месте?"
    if risk_level == "high":
        return "Слышу тебя. Сейчас правда сложно. Расскажи чуть больше — что произошло?"
    if risk_level == "elevated":
        return "Понимаю. Дыши со мной... вдох... выдох. Я рядом."
    return "Привет. Я Кайрос. Что у тебя?"


class MockLLMProvider(BaseLLMProvider):
    """Mock-провайдер. НЕ для production — только для e2e тестов."""

    async def generate(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        extra_body: dict[str, Any] | None = None,
    ) -> LLMResponse:
        # Игнорируем temperature/max_tokens/extra_body — детерминистично
        user_text = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        risk = _detect_risk_level(user_text)

        if _is_analyzer_request(messages):
            text = _build_analyzer_response(risk)
        else:
            text = _build_main_reply(risk)

        return LLMResponse(
            text=text,
            usage=UsageStats(
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                cached_tokens=0,
            ),
            response_time_ms=10.0,
        )

    async def generate_stream(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        extra_body: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Стриминг — отдаём весь текст одним чанком."""
        result = await self.generate(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body=extra_body,
        )
        yield result.text

    async def close(self) -> None:
        """Mock — нет ресурсов для освобождения."""
        return
