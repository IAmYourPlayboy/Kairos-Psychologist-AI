"""POST /api/feedback — обратная связь для data flywheel.

Клиент шлёт сигналы:
- Явные: пользователь нажал «стало легче» / «не помогло» / 👍 / 👎
- Неявные: таймаут сессии, эскалация кризиса (но эти лучше писать с сервера,
  а не получать от клиента — клиент только шлёт явные).

Все события идут в таблицу `feedback_events` для будущего LoRA fine-tuning
(отбор «успешных» / «неуспешных» диалогов).
"""

from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import FeedbackRequest, FeedbackResponse
from app.data.database import get_db
from app.data.models import ChatSession, FeedbackEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest, db: AsyncSession = Depends(get_db)
) -> FeedbackResponse:
    """Сохранить событие обратной связи в БД."""
    # Проверяем что сессия существует
    session = await db.get(ChatSession, request.session_id)
    if session is None:
        raise HTTPException(
            status_code=404, detail="Сессия не найдена"
        )

    feedback_id = str(uuid4())
    event = FeedbackEvent(
        id=feedback_id,
        session_id=request.session_id,
        message_id=request.message_id,
        event_type=request.event_type,
    )
    db.add(event)

    # Если это сигнал улучшения/ухудшения — обновим outcome сессии
    # (последнее значение перевешивает предыдущие, потому что прогресс
    # оценивается по итогу).
    if request.event_type == "felt_better":
        session.outcome = "improved"
    elif request.event_type == "no_change":
        session.outcome = "no_change"
    elif request.event_type == "felt_worse":
        session.outcome = "escalated"
    elif request.event_type == "user_left":
        session.outcome = "left"

    await db.commit()

    logger.info(
        "Feedback: session=%s event=%s",
        request.session_id[:8],
        request.event_type,
    )

    return FeedbackResponse(ok=True, feedback_id=feedback_id)
