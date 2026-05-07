"""Семантические хелперы для extra_body параметра LLM-провайдеров.

Зачем: спрятать «магические строки» в одном месте. В коде вместо
::
    extra_body={"chat_template_kwargs": {"enable_thinking": False}}

будет:
::
    extra_body=disable_reasoning()

При смене провайдера / модели — меняем тут одну функцию, остальной код
работает без изменений.

Источники истины (как разные модели отключают reasoning):
- Qwen 3 / 3.5 / 3.6 в Yandex AI Studio: ``chat_template_kwargs.enable_thinking``
- Qwen open-source vLLM: то же самое
- DeepSeek через Yandex (V3.2): не имеет режима, no-op
- YandexGPT: не имеет режима, no-op
- Будущие OpenAI o1-style модели: ``reasoning.effort = "none"`` (Yandex пока не принимает)

В рантайме применяется только ``chat_template_kwargs``. Если провайдер не
понимает поле, то одно из двух:
- Провайдер игнорирует его (Yandex для не-Qwen моделей)
- Возвращает 400 (Yandex отверг, например, ``enable_thinking`` и ``reasoning``
  как top-level поля)

Поэтому `disable_reasoning()` сейчас возвращает ровно ту структуру, которая
**не отвергается** Yandex и **работает** для Qwen.
"""

from __future__ import annotations

from typing import Any


def disable_reasoning() -> dict[str, Any]:
    """Отключить reasoning mode у модели (для Qwen через Yandex AI Studio).

    Возвращает payload-фрагмент, который:
    - У Qwen 3.x в Yandex: отключает «размышления», модель сразу пишет ответ
    - У других моделей: игнорируется (или может вернуть 400 — но Yandex
      замолчал на ``chat_template_kwargs`` для не-Qwen моделей)

    Использование::

        from app.core.llm.extra_body import disable_reasoning
        response = await provider.generate(
            messages=[...],
            extra_body=disable_reasoning(),
        )
    """
    return {"chat_template_kwargs": {"enable_thinking": False}}


def merge_extra(*parts: dict[str, Any] | None) -> dict[str, Any]:
    """Объединить несколько extra_body в один.

    Полезно когда нужно скомпоновать `disable_reasoning()` + другие опции::

        extra = merge_extra(
            disable_reasoning(),
            {"frequency_penalty": 0.5},
        )

    None-аргументы игнорируются.
    """
    result: dict[str, Any] = {}
    for part in parts:
        if part:
            result.update(part)
    return result
