"""POST /api/chat — главный эндпоинт диалога с ботом.

Поток обработки:
    1. Получить сообщение пользователя
    2. Определить уровень кризиса (assess_crisis_level)
    3. Выбрать ветку (A — мобилизация или B — стабилизация)
    4. Собрать system prompt (с учётом ветки и кризиса)
    5. Сформировать messages = [system, ...history, user]
    6. Вызвать LLM
    7. Сохранить запрос и ответ в БД (data flywheel)
    8. Вернуть клиенту: ответ + crisis_level + контакты

Особое поведение:
    - При crisis_level=immediate — бот всегда даёт контакты, даже если LLM упал.
    - Сессия создаётся автоматически при первом сообщении.
"""

from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    CrisisContactDTO,
)
from app.config import settings
from app.core.branch_selector import select_branch
from app.core.crisis.contacts import get_crisis_contacts
from app.core.crisis.detector import assess_crisis_level
from app.core.llm.base import Message
from app.core.llm.factory import get_provider
from app.core.prompts.builder import build_system_prompt
from app.data.database import get_db
from app.data.models import ChatSession, Message as MessageModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# ============================================================================
# Жёстко-зашитые ответы для критических кейсов
# (используются если LLM недоступен в кризисный момент)
# ============================================================================

_FALLBACK_IMMEDIATE = (
    "Я слышу тебя. Прямо сейчас позвони по одному из этих номеров — "
    "там помогут.\n\n"
    "📞 112 — экстренные службы (работает без SIM)\n"
    "📞 8-800-2000-122 — детский телефон доверия\n"
    "📞 8-800-333-44-34 — психологическая помощь МЧС (круглосуточно, бесплатно)\n\n"
    "Я буду здесь, когда вернёшься."
)

_FALLBACK_GENERIC = (
    "Извини, я сейчас не могу ответить. Попробуй ещё раз через минуту."
)


# ============================================================================
# Эндпоинт
# ============================================================================


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest, db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """Обработать сообщение пользователя и вернуть ответ бота.

    Этот эндпоинт — сердце продукта. Он связывает все компоненты:
    кризисную детекцию, выбор ветки, промпт, LLM и логирование в БД.
    """
    # === 1. Кризисная детекция ===
    crisis_level = assess_crisis_level(request.message)

    # === 2. Выбор ветки ===
    branch = select_branch(request.message)

    # === 3. Кризисные контакты (для ответа клиенту) ===
    crisis_contacts: list[CrisisContactDTO] = []
    if crisis_level != "normal":
        contacts = get_crisis_contacts(request.age_group)
        crisis_contacts = [
            CrisisContactDTO(
                name=c.name, phone=c.phone, description=c.description
            )
            for c in contacts
        ]

    # === 4. Подготовка / создание сессии в БД ===
    session_id = request.session_id or str(uuid4())
    session = await _get_or_create_session(
        db,
        session_id=session_id,
        guest_id=request.guest_id,
        branch=branch,
        crisis_level=crisis_level,
    )

    # === 5. Сохранить пользовательское сообщение ===
    user_message_id = str(uuid4())
    user_msg = MessageModel(
        id=user_message_id,
        session_id=session.id,
        role="user",
        content=request.message,
        crisis_level=crisis_level,
    )
    db.add(user_msg)

    # === 6. Собрать промпт и историю для LLM ===
    system_prompt = build_system_prompt(
        branch=branch,
        crisis_level=crisis_level,
        # Не используем динамический router пока (нет distress_score без NLP).
        # Включится в Блоке 12.
        use_router=False,
    )

    llm_messages: list[Message] = [Message(role="system", content=system_prompt)]
    # Добавляем историю (последние 50 сообщений уже ограничено схемой)
    for hist_msg in request.history:
        llm_messages.append(Message(role=hist_msg.role, content=hist_msg.content))
    # Текущее сообщение пользователя
    llm_messages.append(Message(role="user", content=request.message))

    # === 7. Вызов LLM ===
    reply_text, metrics = await _call_llm_with_fallback(
        llm_messages=llm_messages,
        crisis_level=crisis_level,
    )

    # === 8. Сохранить ответ бота ===
    bot_message_id = str(uuid4())
    bot_msg = MessageModel(
        id=bot_message_id,
        session_id=session.id,
        role="assistant",
        content=reply_text,
        crisis_level=crisis_level,
        response_time_ms=metrics.get("response_time_ms"),
        prompt_tokens=metrics.get("prompt_tokens"),
        completion_tokens=metrics.get("completion_tokens"),
    )
    db.add(bot_msg)

    # === 9. Обновить счётчик сообщений сессии ===
    session.message_count += 2  # user + assistant
    # Поднимаем максимальный кризис если сейчас выше
    if _crisis_priority(crisis_level) > _crisis_priority(session.crisis_level_max):
        session.crisis_level_max = crisis_level

    await db.commit()

    logger.info(
        "Chat: session=%s branch=%s crisis=%s reply_len=%d response_ms=%s",
        session.id[:8],
        branch,
        crisis_level,
        len(reply_text),
        metrics.get("response_time_ms"),
    )

    return ChatResponse(
        reply=reply_text,
        session_id=session.id,
        message_id=bot_message_id,
        crisis_level=crisis_level,
        crisis_contacts=crisis_contacts,
        branch=branch,
        response_time_ms=metrics.get("response_time_ms"),
        prompt_tokens=metrics.get("prompt_tokens"),
        completion_tokens=metrics.get("completion_tokens"),
        # llm_error пробрасываем только в debug-режиме (для разработки)
        llm_error=metrics.get("llm_error") if settings.debug else None,
    )


# ============================================================================
# Вспомогательные функции
# ============================================================================


async def _get_or_create_session(
    db: AsyncSession,
    *,
    session_id: str,
    guest_id: str | None,
    branch: str,
    crisis_level: str,
) -> ChatSession:
    """Получить существующую сессию или создать новую.

    Сессия идентифицируется по session_id (генерируется на клиенте).
    Если её ещё нет в БД — создаём.
    """
    existing = await db.get(ChatSession, session_id)
    if existing is not None:
        return existing

    new_session = ChatSession(
        id=session_id,
        guest_id=guest_id,
        branch=branch,
        crisis_level_max=crisis_level,
        message_count=0,
    )
    db.add(new_session)
    # Flush чтобы можно было ссылаться на session.id ниже до commit
    await db.flush()
    return new_session


def _crisis_priority(level: str) -> int:
    """Числовой приоритет уровня кризиса (для сравнения)."""
    return {"normal": 0, "elevated": 1, "high": 2, "immediate": 3}.get(level, 0)


async def _call_llm_with_fallback(
    llm_messages: list[Message],
    crisis_level: str,
) -> tuple[str, dict]:
    """Вызвать LLM с обработкой ошибок.

    При ошибке LLM:
    - Если crisis = immediate → жёстко-зашитый кризисный ответ с контактами
    - Иначе → общий ответ-заглушка

    Returns:
        (текст_ответа, метрики_dict)
    """
    import httpx

    metrics: dict = {}
    start = time.perf_counter()

    try:
        provider = get_provider()
        response = await provider.generate(llm_messages)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        metrics["response_time_ms"] = elapsed_ms
        metrics["prompt_tokens"] = response.usage.prompt_tokens
        metrics["completion_tokens"] = response.usage.completion_tokens
        return response.text, metrics

    except httpx.HTTPStatusError as e:
        # HTTP-ошибка от LLM API: логируем и тело ответа (для отладки)
        body_preview = ""
        try:
            body_preview = e.response.text[:500]
        except Exception:
            pass
        logger.error(
            "LLM HTTP error: status=%d url=%s body=%s",
            e.response.status_code,
            e.request.url,
            body_preview,
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        metrics["response_time_ms"] = elapsed_ms
        metrics["llm_error"] = (
            f"HTTP {e.response.status_code}: {body_preview[:200]}"
        )

    except httpx.HTTPError as e:
        # Сетевая ошибка / таймаут / неверный URL
        logger.exception("LLM network error: %s", e)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        metrics["response_time_ms"] = elapsed_ms
        metrics["llm_error"] = f"Network: {type(e).__name__}: {e}"

    except Exception as e:
        # Любая другая неожиданная ошибка
        logger.exception("LLM unexpected error: %s", e)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        metrics["response_time_ms"] = elapsed_ms
        metrics["llm_error"] = f"Unexpected: {type(e).__name__}: {e}"

    # Fallback: при immediate — жёстко-зашитый кризисный ответ
    if crisis_level == "immediate":
        return _FALLBACK_IMMEDIATE, metrics
    return _FALLBACK_GENERIC, metrics
