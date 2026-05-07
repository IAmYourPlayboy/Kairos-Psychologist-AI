"""MessageAnalyzer — отдельный LLM-вызов на каждое сообщение.

Дизайн: §5 в spec.

Поведение:
- Получает текущее сообщение, историю и выжимку досье.
- Делает один LLM-вызов с системным промптом (analyzer_prompt.py).
- Парсит JSON-ответ в PerceptionReport.
- Не глотает исключения LLM (по дизайн-решению §9: упало — упало,
  основной поток разберётся и ответит «извини, не могу»).

НЕ хранит состояния. Один и тот же экземпляр можно вызывать конкурентно.
"""

from __future__ import annotations

import json
import logging
import re

from pydantic import ValidationError

from app.core.llm.base import Message
from app.core.llm.extra_body import disable_reasoning
from app.core.llm.factory import get_provider
from app.core.perception.analyzer_prompt import (
    ANALYZER_SYSTEM_PROMPT,
    build_analyzer_user_prompt,
)
from app.core.perception.types import PerceptionReport

logger = logging.getLogger(__name__)


class AnalyzerError(Exception):
    """Ошибка парсинга или валидации ответа анализатора.

    В отличие от исключений LLM (HTTPError, RuntimeError) — это
    индикатор «LLM ответил, но не так как нужно». Эти ошибки могут
    указывать на проблемы с промптом или с моделью.
    """


# Регулярка для снятия ```json ... ``` обёртки если LLM её добавил.
_MARKDOWN_JSON_FENCE = re.compile(
    r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL,
)


def strip_markdown_fence(text: str) -> str:
    """Снять ```json ... ``` или ``` ... ``` обёртку, если есть.

    Public helper — переиспользуется в ReflectionAgent (Фаза 5)
    для парсинга JSON, который тоже может приходить в обёртке.
    """
    text = text.strip()
    m = _MARKDOWN_JSON_FENCE.match(text)
    if m:
        return m.group(1).strip()
    return text


class MessageAnalyzer:
    """Анализатор сообщений. См. spec §5."""

    def __init__(self, *, temperature: float = 0.3, max_tokens: int = 800):
        # Невысокая температура — нам нужны стабильные структурированные ответы.
        # max_tokens с запасом на JSON + inner_monologue.
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def analyze(
        self,
        *,
        current_message: str,
        history: list[dict[str, str]],
        dossier_summary: str,
    ) -> PerceptionReport:
        """Проанализировать одно сообщение пользователя.

        Args:
            current_message: текст текущего сообщения.
            history: список последних реплик [{"role": "user|assistant", "content": "..."}].
            dossier_summary: текстовая выжимка досье (или "пусто").

        Returns:
            PerceptionReport.

        Raises:
            AnalyzerError: если LLM вернул невалидный JSON / схему.
            Прочие исключения LLM — пробрасываются как есть.
        """
        provider = get_provider()
        user_prompt = build_analyzer_user_prompt(
            current_message=current_message,
            history=history,
            dossier_summary=dossier_summary,
        )

        messages = [
            Message(role="system", content=ANALYZER_SYSTEM_PROMPT),
            Message(role="user", content=user_prompt),
        ]

        # Отключаем reasoning mode: анализатору нужен короткий JSON, размышления
        # съели бы токены и удвоили latency. Параметр игнорируется провайдерами,
        # которые не поддерживают reasoning (YandexGPT и т.д.).
        response = await provider.generate(
            messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            extra_body=disable_reasoning(),
        )

        # 1. Снять markdown-обёртку если есть
        raw = strip_markdown_fence(response.text)

        # 2. Распарсить JSON
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning(
                "Analyzer returned non-JSON: %s (preview: %r)",
                e, raw[:200],
            )
            raise AnalyzerError(
                f"Не удалось распарсить JSON анализатора: {e}",
            ) from e

        # 3. Валидировать через Pydantic
        try:
            report = PerceptionReport(**data)
        except ValidationError as e:
            logger.warning(
                "Analyzer JSON failed schema validation: %s (data keys: %s)",
                e, list(data.keys()) if isinstance(data, dict) else type(data),
            )
            raise AnalyzerError(
                f"JSON анализатора не соответствует схеме: {e}",
            ) from e

        return report
