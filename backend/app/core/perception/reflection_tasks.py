"""Celery-таск для запуска ReflectionAgent.

Запускается отложенно через 15 минут после последнего сообщения
пользователя (см. settings.reflection_delay_seconds).

Дедупликация: используем Redis-ключ reflection:scheduled:{user_id} с TTL.
- При каждом сообщении пользователя в Redis записывается новый
  scheduled_at (ISO timestamp) и Celery планируется через countdown.
- Когда таск выстреливает, он проверяет: scheduled_at в Redis совпадает
  с тем, с которым он был запущен? Если нет — это значит был более свежий
  запрос, наш таск устарел, выходим.

Это позволяет «сдвигать» окно ожидания: пока пользователь продолжает
печатать, таск откладывается; срабатывает только когда пользователь
реально замолкает на 15+ минут.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Celery-таск
# ============================================================================


@celery_app.task(
    name="app.core.perception.reflection_tasks.run_reflection",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def run_reflection(self, user_id: str, scheduled_at: str) -> dict:
    """Celery-обёртка над ReflectionAgent.run_for_user.

    Args:
        user_id: id пользователя.
        scheduled_at: ISO timestamp когда был запланирован запуск.
                      Используется для дедупликации.

    Returns:
        Словарь с метриками для celery result backend.
    """
    return asyncio.run(_run_async(user_id, scheduled_at))


async def _run_async(user_id: str, scheduled_at: str) -> dict:
    """Async-обёртка для вызова из синхронного celery-таска."""
    # Импорты внутри функции — чтобы Celery worker не падал на старте
    # если эти модули по какой-то причине ломаются (изоляция).
    from app.core.perception.redis_client import get_redis
    from app.core.perception.reflection_agent import ReflectionAgent
    from app.data.database import async_session_factory

    redis = get_redis()
    key = f"reflection:scheduled:{user_id}"

    # Дедупликация: проверяем что наш scheduled_at — самый свежий
    current = await redis.get(key)
    if current is not None:
        current_str = (
            current.decode() if isinstance(current, (bytes, bytearray)) else current
        )
        if current_str != scheduled_at:
            logger.info(
                "Reflection skipped (stale): user=%s ours=%s current=%s",
                user_id[:8], scheduled_at, current_str,
            )
            return {"skipped": "stale_schedule"}

    # Запускаем
    async with async_session_factory() as db:
        agent = ReflectionAgent(db=db)
        result = await agent.run_for_user(user_id)

    # Снимаем флаг (он уже отработал)
    await redis.delete(key)

    return {
        "user_id": user_id,
        "facts_created": result.facts_created,
        "facts_updated": result.facts_updated,
        "facts_superseded": result.facts_superseded,
        "candidates_total": result.candidates_total,
        "candidates_skipped": result.candidates_skipped,
        "skipped_reason": result.skipped_reason,
    }


# ============================================================================
# Scheduling helper (вызывается из chat.py после каждого сообщения)
# ============================================================================


async def schedule_reflection(user_id: str) -> None:
    """Запланировать (или перепланировать) reflection для пользователя.

    Логика:
    - Записываем в Redis новый scheduled_at timestamp.
    - Запускаем Celery-таск с countdown=settings.reflection_delay_seconds.
    - Когда таск выстрелит — проверит, совпадает ли timestamp в Redis с тем,
      с которым он был запущен. Если нет — значит был новый запрос,
      устарел, выходим.

    Args:
        user_id: id пользователя. Если None/пусто — рефлексия не делается
                 (гость без user_id, нет куда писать досье).
    """
    if not user_id:
        return

    from app.core.perception.redis_client import get_redis

    redis = get_redis()
    key = f"reflection:scheduled:{user_id}"
    scheduled_at = datetime.now(timezone.utc).isoformat()

    # TTL ставим с запасом — 2× от delay, чтобы ключ не протух раньше таска
    await redis.set(
        key, scheduled_at,
        ex=settings.reflection_delay_seconds * 2,
    )

    run_reflection.apply_async(
        args=[user_id, scheduled_at],
        countdown=settings.reflection_delay_seconds,
        queue="reflection",
    )
    logger.info(
        "Reflection scheduled: user=%s in %ds",
        user_id[:8], settings.reflection_delay_seconds,
    )
