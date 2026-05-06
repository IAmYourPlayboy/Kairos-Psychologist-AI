"""Утилита: вызвать ReflectionAgent extract напрямую с реальным LLM
на тестовых сообщениях, увидеть сырой ответ модели.

Полезно для отладки: понять, ВОЗВРАЩАЕТ ли модель вообще что-то осмысленное
на наш промпт, и в каком формате.

Запуск (из backend/, с активированным venv):
    python scripts/test_extract_live.py
"""

from __future__ import annotations

import asyncio
import sys

from app.core.llm.base import Message
from app.core.llm.factory import get_provider
from app.core.perception.reflection_prompt import (
    EXTRACT_SYSTEM_PROMPT,
    build_extract_user_prompt,
)


def _print(s: str) -> None:
    sys.stdout.buffer.write((s + "\n").encode("utf-8"))


# Тестовые сообщения (с фейковыми message_id)
SAMPLE_MESSAGES = [
    ("msg-001", "у меня есть младший брат Егор"),
    ("msg-002", "папа иногда выпивает по выходным"),
    ("msg-003", "я общаюсь с тобой каждый день в 20:00, это уже как ритуал"),
]


async def main() -> None:
    block = "\n".join(
        f"[message_id={mid}] {content}"
        for mid, content in SAMPLE_MESSAGES
    )

    user_prompt = build_extract_user_prompt(
        messages_block=block,
        existing_dossier_summary="(пусто — досье ещё не наполнено)",
    )

    _print("=" * 70)
    _print("Отправляю запрос в LLM extract-этапа...")
    _print("=" * 70)

    provider = get_provider()
    response = await provider.generate(
        [
            Message(role="system", content=EXTRACT_SYSTEM_PROMPT),
            Message(role="user", content=user_prompt),
        ],
        temperature=0.2,
        max_tokens=2000,
    )

    _print("")
    _print("=== СЫРОЙ ОТВЕТ LLM ===")
    _print(response.text)
    _print("")
    _print(f"=== prompt_tokens: {response.usage.prompt_tokens}")
    _print(f"=== completion_tokens: {response.usage.completion_tokens}")
    _print(f"=== response_time_ms: {response.response_time_ms}")

    # Попробуем распарсить
    import json
    from app.core.perception.analyzer import strip_markdown_fence

    raw = strip_markdown_fence(response.text)
    _print("")
    _print("=== ПОПЫТКА ПАРСИНГА ===")
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            _print(f"OK — массив из {len(data)} элементов")
            for i, item in enumerate(data):
                _print(f"  [{i}] {item.get('summary', '<no summary>')}")
        else:
            _print(f"FAIL — JSON распарсился, но это {type(data).__name__}, а не массив")
    except json.JSONDecodeError as e:
        _print(f"FAIL — не валидный JSON: {e}")
        _print(f"первые 500 символов raw: {raw[:500]!r}")

    await provider.close()


if __name__ == "__main__":
    asyncio.run(main())
