"""Глобальный async Redis-клиент для слоя восприятия.

Создаётся один раз при старте приложения, закрывается при shutdown.
Используется и для Mood (Фаза 3), и для отложенного запуска
ReflectionAgent (Фаза 5).
"""

from __future__ import annotations

import logging

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """Вернуть singleton Redis-клиент.

    Создаётся при первом обращении. Не закрывает сам себя — закрытие
    через close_redis() в lifespan.
    """
    global _client
    if _client is None:
        _client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            # Не декодировать в строку: MoodService и так делает json.loads,
            # а fakeredis в тестах возвращает bytes.
            decode_responses=False,
        )
        logger.info("Redis client created: %s", settings.redis_url)
    return _client


async def close_redis() -> None:
    """Закрыть пул соединений Redis. Вызывается в lifespan на shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("Redis client closed")
