"""POST /api/chat — главный эндпоинт диалога с ботом.

Поток обработки (Сессия 18+, после удаления rule-based слоя):

1. PerceptionPipeline.process_message():
   - MessageAnalyzer (LLM-вызов) → PerceptionReport
     (risk_level + emotion + theme + folder_hints + ...)
   - MoodService.update_from_report → 6 осей в Redis
   - Подтяжка релевантных фактов по folder_hints
   - PromptBuilder → главный system prompt
   - Основная LLM → reply
2. crisis_level берётся из report.risk_level.
3. perception_json сохраняется в user_msg для data flywheel.
4. Никакого rule-based fallback — при ошибке честное «извини, не могу»
   (по дизайн-решению §9 spec).
5. После commit'а планируется ReflectionAgent через 15 минут (если есть user_id).

Сессия создаётся автоматически при первом сообщении.
"""

from __future__ import annotations

import logging
from uuid import uuid4

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    CrisisContactDTO,
)
from app.config import settings
from app.core.auth.dependencies import get_optional_user
from app.core.crisis.contacts import get_crisis_contacts
from app.data.database import get_db
from app.data.models import ChatSession, Message as MessageModel, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# Текст для пользователя, когда PerceptionPipeline упал.
# Это единственный «fallback» теперь: честное сообщение и SOS-кнопка
# в UI остаётся доступна со статичными контактами.
_PERCEPTION_FALLBACK = (
    "Извини, я сейчас не могу отвечать. "
    "Если это срочно — нажми SOS вверху для номеров помощи."
)


# ============================================================================
# Эндпоинт
# ============================================================================


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> ChatResponse:
    """Обработать сообщение пользователя и вернуть ответ бота.

    Этот эндпоинт — сердце продукта. Связывает все компоненты слоя
    восприятия: анализатор, mood, досье, промпт-сборку, LLM и
    логирование в БД.

    Работает и для гостей (user None), и для залогиненных. Единственное
    исключение: если у залогиненного запланировано удаление аккаунта —
    блокируем чат с инструкцией восстановить.
    """
    # === 0. Блокировка для pending-deletion пользователей ===
    if current_user is not None and current_user.deletion_scheduled_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "account_pending_deletion",
                "message": (
                    "Твой аккаунт помечен на удаление. Чтобы продолжить — "
                    "отмени удаление в настройках профиля."
                ),
                "scheduled_at": current_user.deletion_scheduled_at.isoformat(),
            },
        )

    # === 1. Подготовка / создание сессии ===
    session_id = request.session_id or str(uuid4())
    session = await _get_or_create_session(
        db,
        session_id=session_id,
        guest_id=request.guest_id,
    )

    # === 2. Сохранить пользовательское сообщение (ОРИГИНАЛЬНЫЙ ТЕКСТ) ===
    # Анонимизация ПДн делается асинхронно ReflectionAgent через 15 минут
    # после последнего сообщения (Сессия 22, B1 решение):
    #   - ReflectionAgent видит весь диалог → контекстная анонимизация
    #     (один и тот же «папа» в разных сообщениях помечается одинаково)
    #   - LLM-проход поверх regex даёт точнее результат, чем словарный
    #     метод на одном сообщении
    #   - /api/chat остаётся быстрым, без лишнего CPU на горячем пути
    # Юридически (ФЗ-152 ст.10): бекенд в РФ + явное согласие + окно до
    # анонимизации ≤15 мин. Бэкапы — раз в сутки, окно перекрывает.
    user_message_id = str(uuid4())
    user_msg = MessageModel(
        id=user_message_id,
        session_id=session.id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)

    # === 3. Прогон через PerceptionPipeline ===
    reply_text, metrics, crisis_level, perception_json = (
        await _process_with_perception_layer(
            db=db,
            session=session,
            user_message=request.message,
            history=[
                {"role": h.role, "content": h.content}
                for h in request.history
            ],
            age_group=request.age_group,
        )
    )
    user_msg.perception_json = perception_json
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

    # === 6. Обновить счётчик и максимальный кризис сессии ===
    session.message_count += 2  # user + assistant
    if _crisis_priority(crisis_level) > _crisis_priority(session.crisis_level_max):
        session.crisis_level_max = crisis_level

    await db.commit()

    # === 7. Запланировать рефлексию через 15 минут (если есть user_id) ===
    # ReflectionAgent сам понимает stale-расписание: если пользователь
    # продолжает писать, новый scheduled_at перебьёт старый и таск-старичок
    # выйдет ничего не сделав.
    if session.user_id:
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
        "Chat: session=%s crisis=%s reply_len=%d response_ms=%s",
        session.id[:8],
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
        # branch больше не используется (Сессия 18+, удалён rule-based селектор).
        # Оставляем поле в схеме как None для бэк-совместимости со старыми
        # клиентами. После Блока 13 поле уйдёт из схемы.
        branch=None,
        response_time_ms=metrics.get("response_time_ms"),
        prompt_tokens=metrics.get("prompt_tokens"),
        completion_tokens=metrics.get("completion_tokens"),
        llm_error=metrics.get("llm_error") if settings.debug else None,
    )


# ============================================================================
# Реализация PerceptionPipeline-вызова
# ============================================================================


async def _process_with_perception_layer(
    *,
    db: AsyncSession,
    session: ChatSession,
    user_message: str,
    history: list[dict[str, str]],
    age_group: str | None = None,
) -> tuple[str, dict, str, str | None]:
    """Прогнать сообщение через PerceptionPipeline.

    Args:
        age_group: возрастная группа пользователя ("child"/"youth"/"adult"/None).
            Определяет какие кризисные контакты попадут в промпт при
            risk_level != normal. Берётся из ChatRequest.age_group.

    Returns:
        (reply_text, metrics, crisis_level, perception_json)
    """
    # Импорты внутри функции, чтобы Redis-клиент создавался лениво
    # (модуль chat.py может быть импортирован при тестах без Redis).
    from app.core.perception.pipeline import PerceptionPipeline
    from app.core.perception.redis_client import get_redis

    metrics: dict = {}

    try:
        pipeline = PerceptionPipeline(db=db, redis_client=get_redis())
        result = await pipeline.process_message(
            user_id=session.user_id,
            guest_id=session.guest_id,
            session_id=session.id,
            user_message=user_message,
            history=history,
            age_group=age_group,
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
        # По дизайн-решению §9 spec: rule-based fallback нет.
        # Честное сообщение пользователю + SOS-кнопка в UI остаётся.
        logger.exception("Perception pipeline failed: %s", e)
        metrics["llm_error"] = (
            f"perception_failed: {type(e).__name__}: {e}"
        )
        return _PERCEPTION_FALLBACK, metrics, "normal", None


# ============================================================================
# Вспомогательные функции
# ============================================================================


async def _get_or_create_session(
    db: AsyncSession,
    *,
    session_id: str,
    guest_id: str | None,
) -> ChatSession:
    """Получить существующую сессию или создать новую."""
    existing = await db.get(ChatSession, session_id)
    if existing is not None:
        return existing

    new_session = ChatSession(
        id=session_id,
        guest_id=guest_id,
        crisis_level_max="normal",
        message_count=0,
    )
    db.add(new_session)
    await db.flush()
    return new_session


def _crisis_priority(level: str) -> int:
    """Числовой приоритет уровня кризиса (для сравнения)."""
    return {"normal": 0, "elevated": 1, "high": 2, "immediate": 3}.get(level, 0)
