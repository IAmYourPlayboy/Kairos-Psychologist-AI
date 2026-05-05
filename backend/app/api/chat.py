"""POST /api/chat — главный эндпоинт диалога с ботом.

Имеет ДВА режима, переключаемых флагом settings.use_perception_layer:

**Старый режим** (use_perception_layer = False):
1. Rule-based assess_crisis_level → уровень кризиса
2. Rule-based select_branch → A или B
3. build_system_prompt(branch, crisis_level)
4. LLM-вызов
5. Fallback в _call_llm_with_fallback при ошибках

**Новый режим** (use_perception_layer = True, Сессия 18+):
1. PerceptionPipeline.process_message():
   - MessageAnalyzer (LLM-вызов) → PerceptionReport (risk + emotion + theme + ...)
   - MoodService.update_from_report → 6 осей в Redis
   - Подтяжка релевантных фактов по folder_hints
   - PromptBuilder → main system prompt
   - Основная LLM → reply
2. crisis_level берётся из report.risk_level
3. perception_json сохраняется в user_msg для data flywheel
4. Никакого rule-based fallback — при ошибке честное «извини, не могу»

Сессия создаётся автоматически при первом сообщении.

Старая ветка удаляется в Фазе 6 после проверки нового слоя.
"""

from __future__ import annotations

import logging
import time
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends
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
# Жёстко-зашитые ответы для критических кейсов (только для старой ветки!)
# Новая ветка таких fallback не имеет (по дизайн-решению §9 spec).
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

# Текст для нового слоя, когда что-то пошло не так
_PERCEPTION_FALLBACK = (
    "Извини, я сейчас не могу отвечать. "
    "Если это срочно — нажми SOS вверху для номеров помощи."
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
    # === 1. Подготовка / создание сессии ===
    session_id = request.session_id or str(uuid4())
    # branch и crisis_level — НЕ финальные, заполнятся после анализа.
    # Для новой ветки branch будет None.
    initial_branch: str | None = None
    initial_crisis = "normal"
    if not settings.use_perception_layer:
        # В старой ветке считаем сразу для совместимости
        initial_crisis = assess_crisis_level(request.message)
        initial_branch = select_branch(request.message)

    session = await _get_or_create_session(
        db,
        session_id=session_id,
        guest_id=request.guest_id,
        branch=initial_branch,
        crisis_level=initial_crisis,
    )

    # === 2. Сохранить пользовательское сообщение (без crisis_level пока) ===
    user_message_id = str(uuid4())
    user_msg = MessageModel(
        id=user_message_id,
        session_id=session.id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)

    # === 3. Развилка: новый слой восприятия ИЛИ старый rule-based ===
    if settings.use_perception_layer:
        reply_text, metrics, crisis_level, perception_json = (
            await _process_with_perception_layer(
                db=db,
                session=session,
                user_message=request.message,
                history=[
                    {"role": h.role, "content": h.content}
                    for h in request.history
                ],
            )
        )
        user_msg.perception_json = perception_json
        # branch в новом слое не используется
        branch_for_response: str | None = None
    else:
        reply_text, metrics, crisis_level = await _process_with_legacy_pipeline(
            user_message=request.message,
            history=request.history,
            initial_branch=initial_branch or "B",
            initial_crisis=initial_crisis,
        )
        branch_for_response = initial_branch

    # Финализируем crisis_level в user_msg (теперь он точно известен)
    user_msg.crisis_level = crisis_level

    # === 4. Кризисные контакты (на основе финального crisis_level) ===
    crisis_contacts: list[CrisisContactDTO] = []
    if crisis_level != "normal":
        contacts = get_crisis_contacts(request.age_group)
        crisis_contacts = [
            CrisisContactDTO(
                name=c.name, phone=c.phone, description=c.description,
            )
            for c in contacts
        ]

    # === 5. Сохранить ответ бота ===
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

    # === 6. Обновить счётчик сообщений сессии ===
    session.message_count += 2  # user + assistant
    if _crisis_priority(crisis_level) > _crisis_priority(session.crisis_level_max):
        session.crisis_level_max = crisis_level

    await db.commit()

    # === 7. Запланировать рефлексию через 15 минут ===
    # Только если включён слой восприятия и есть user_id (не гость).
    # ReflectionAgent сам понимает stale-расписание: если пользователь
    # продолжает писать, новый scheduled_at перебьёт старый и таск-старичок
    # выйдет ничего не сделав.
    if settings.use_perception_layer and session.user_id:
        try:
            from app.core.perception.reflection_tasks import schedule_reflection
            await schedule_reflection(session.user_id)
        except Exception:
            # Если Celery/Redis недоступны — не валим основной поток.
            # Без рефлексии бот всё равно отвечает, досье просто не наполнится.
            logger.exception(
                "Failed to schedule reflection (non-fatal)",
            )

    logger.info(
        "Chat: session=%s perception=%s crisis=%s reply_len=%d response_ms=%s",
        session.id[:8],
        settings.use_perception_layer,
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
        branch=branch_for_response,
        response_time_ms=metrics.get("response_time_ms"),
        prompt_tokens=metrics.get("prompt_tokens"),
        completion_tokens=metrics.get("completion_tokens"),
        llm_error=metrics.get("llm_error") if settings.debug else None,
    )


# ============================================================================
# Реализации двух веток
# ============================================================================


async def _process_with_perception_layer(
    *,
    db: AsyncSession,
    session: ChatSession,
    user_message: str,
    history: list[dict[str, str]],
) -> tuple[str, dict, str, str | None]:
    """Новая ветка через PerceptionPipeline.

    Returns:
        (reply_text, metrics, crisis_level, perception_json)
    """
    # Импорты внутри функции, чтобы не тянуть Redis при выключенном флаге
    from app.core.perception.pipeline import PerceptionPipeline
    from app.core.perception.redis_client import get_redis

    metrics: dict = {}

    try:
        pipeline = PerceptionPipeline(db=db, redis_client=get_redis())
        result = await pipeline.process_message(
            user_id=session.user_id,
            session_id=session.id,
            user_message=user_message,
            history=history,
        )
        metrics["response_time_ms"] = result.response_time_ms
        metrics["prompt_tokens"] = result.prompt_tokens
        metrics["completion_tokens"] = result.completion_tokens
        return (
            result.reply,
            metrics,
            result.report.risk_level,
            result.report.model_dump_json(),
        )

    except Exception as e:  # noqa: BLE001 — мы намеренно ловим всё
        # По дизайн-решению §9: rule-based fallback нет.
        # Честное сообщение пользователю.
        logger.exception("Perception pipeline failed: %s", e)
        metrics["llm_error"] = f"perception_failed: {type(e).__name__}: {e}"
        return _PERCEPTION_FALLBACK, metrics, "normal", None


async def _process_with_legacy_pipeline(
    *,
    user_message: str,
    history,  # list[ChatMessageHistory] из request
    initial_branch: str,
    initial_crisis: str,
) -> tuple[str, dict, str]:
    """Старая ветка через rule-based детектор + branch_selector.

    Returns:
        (reply_text, metrics, crisis_level)
    """
    system_prompt = build_system_prompt(
        branch=initial_branch,
        crisis_level=initial_crisis,
        use_router=False,
    )

    llm_messages: list[Message] = [
        Message(role="system", content=system_prompt),
    ]
    for hist_msg in history:
        llm_messages.append(
            Message(role=hist_msg.role, content=hist_msg.content),
        )
    llm_messages.append(Message(role="user", content=user_message))

    reply_text, metrics = await _call_llm_with_fallback(
        llm_messages=llm_messages,
        crisis_level=initial_crisis,
    )
    return reply_text, metrics, initial_crisis


# ============================================================================
# Вспомогательные функции
# ============================================================================


async def _get_or_create_session(
    db: AsyncSession,
    *,
    session_id: str,
    guest_id: str | None,
    branch: str | None,
    crisis_level: str,
) -> ChatSession:
    """Получить существующую сессию или создать новую."""
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
    await db.flush()
    return new_session


def _crisis_priority(level: str) -> int:
    """Числовой приоритет уровня кризиса (для сравнения)."""
    return {"normal": 0, "elevated": 1, "high": 2, "immediate": 3}.get(level, 0)


async def _call_llm_with_fallback(
    llm_messages: list[Message],
    crisis_level: str,
) -> tuple[str, dict]:
    """Вызвать LLM с обработкой ошибок (только для старой ветки).

    При ошибке LLM:
    - Если crisis = immediate → жёстко-зашитый кризисный ответ с контактами
    - Иначе → общий ответ-заглушка
    """
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
        logger.exception("LLM network error: %s", e)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        metrics["response_time_ms"] = elapsed_ms
        metrics["llm_error"] = f"Network: {type(e).__name__}: {e}"

    except Exception as e:  # noqa: BLE001
        logger.exception("LLM unexpected error: %s", e)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        metrics["response_time_ms"] = elapsed_ms
        metrics["llm_error"] = f"Unexpected: {type(e).__name__}: {e}"

    # Fallback: при immediate — жёстко-зашитый кризисный ответ
    if crisis_level == "immediate":
        return _FALLBACK_IMMEDIATE, metrics
    return _FALLBACK_GENERIC, metrics
