"""ScreeningService — CRUD над результатами опросников + frequency cap.

Хранение:
- ScreeningResult (PostgreSQL/SQLite) — постоянное хранение результатов.
  Поле raw_answers — JSON-строка (для совместимости с SQLite).
- Redis — флаг «опросник был предложен этому идентификатору» (TTL 7 дней).
  Это нужно frontend'у, чтобы не предлагать опросник повторно каждый день.

Архитектурные ADR (см. CLAUDE.md и spec):
- ADR-1: ASQ-positive override risk_level=immediate в течение 7 дней.
- ADR-3: frequency cap опросников — через Redis с TTL.
- ADR-4: общая модель ScreeningResult для всех опросников (не отдельные таблицы).
- ADR-5: query'и принимают и user_id, и guest_id (анонимные пользователи).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Protocol

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.screening.asq import ASQAnswer, ASQResult, score_asq
from app.core.screening.pss4 import PSS4Result, score_pss4
from app.data.models import ChatSession, ScreeningResult

logger = logging.getLogger(__name__)


# ============================================================================
# Константы
# ============================================================================


# Окно действия ASQ-positive результата (override risk_level)
ASQ_OVERRIDE_DAYS: int = 7

# TTL флага «опросник был предложен» в Redis
OFFERED_TTL_SECONDS: int = 7 * 24 * 60 * 60  # 7 дней

# Допустимые типы опросников (для валидации входных параметров)
VALID_QUESTIONNAIRES: frozenset[str] = frozenset({"asq", "pss4", "osr"})


# ============================================================================
# Протокол Redis-клиента (минимальный интерфейс)
# ============================================================================


class _RedisLike(Protocol):
    """Минимальный интерфейс. Совместим и с redis.asyncio, и с fakeredis."""

    async def get(self, key: str) -> bytes | None: ...
    async def set(self, key: str, value: str, ex: int | None = None) -> bool: ...
    async def exists(self, *keys: str) -> int: ...


def _offered_key(identifier: str, questionnaire: str) -> str:
    """Ключ Redis для флага «опросник предложен»."""
    return f"screening_offered:{identifier}:{questionnaire}"


# ============================================================================
# Утилита: aware-datetime для сравнений (SQLite naive ↔ PostgreSQL aware)
# ============================================================================


def _ensure_aware(dt: datetime) -> datetime:
    """SQLite не сохраняет таймзону; принудительно интерпретируем как UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ============================================================================
# Сервис
# ============================================================================


class ScreeningService:
    """Сервис над таблицей ScreeningResult и Redis-флагами.

    Stateless относительно сервиса; всё состояние — в БД и Redis.

    Args:
        db: AsyncSession (per-request).
        redis_client: совместимый с redis.asyncio.Redis клиент.
    """

    def __init__(self, db: AsyncSession, redis_client: _RedisLike):
        self._db = db
        self._redis = redis_client

    # ------------------------------------------------------------------
    # Сохранение результатов
    # ------------------------------------------------------------------

    async def save_asq(
        self,
        *,
        session_id: str,
        answers: dict[int, ASQAnswer],
    ) -> tuple[ASQResult, ScreeningResult]:
        """Засчитать ASQ и сохранить запись в БД.

        Args:
            session_id: ID существующей ChatSession (для FK).
            answers: словарь {qid: "yes"|"no"|"decline"}.

        Returns:
            (ASQResult, ORM-запись ScreeningResult).

        Raises:
            ValueError: при ошибках валидации (см. score_asq).
        """
        result = score_asq(answers)

        record = ScreeningResult(
            session_id=session_id,
            questionnaire="asq",
            raw_answers=json.dumps(answers, ensure_ascii=False),
            score=float(result.score),
            interpretation=result.interpretation,
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)

        logger.info(
            "ASQ saved: session=%s interpretation=%s positive=%s",
            session_id[:8], result.interpretation, result.is_positive,
        )

        return result, record

    async def save_pss4(
        self,
        *,
        session_id: str,
        answers: dict[int, int],
    ) -> tuple[PSS4Result, ScreeningResult]:
        """Засчитать PSS-4 и сохранить запись в БД.

        Args:
            session_id: ID существующей ChatSession.
            answers: словарь {qid: 0..4}.

        Returns:
            (PSS4Result, ORM-запись).
        """
        result = score_pss4(answers)

        record = ScreeningResult(
            session_id=session_id,
            questionnaire="pss4",
            raw_answers=json.dumps(answers, ensure_ascii=False),
            score=float(result.score),
            interpretation=result.interpretation,
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)

        logger.info(
            "PSS-4 saved: session=%s score=%d interpretation=%s",
            session_id[:8], result.score, result.interpretation,
        )

        return result, record

    # ------------------------------------------------------------------
    # ASQ-override: главный hot-path для PerceptionPipeline
    # ------------------------------------------------------------------

    async def get_active_asq_positive(
        self,
        *,
        user_id: str | None,
        guest_id: str | None,
        within_days: int = ASQ_OVERRIDE_DAYS,
    ) -> ScreeningResult | None:
        """Найти самый свежий ASQ-positive за N дней у user/guest.

        JOIN на chat_sessions (через session_id) с фильтром по user_id или
        guest_id. interpretation IN {non_acute_positive, acute_positive}.

        Args:
            user_id: id зарегистрированного пользователя (или None).
            guest_id: id анонимного пользователя (или None).
            within_days: окно действия результата (по умолчанию 7).

        Returns:
            Самый свежий positive результат или None.
        """
        if not user_id and not guest_id:
            return None

        cutoff = datetime.now(timezone.utc) - timedelta(days=within_days)

        stmt = (
            select(ScreeningResult)
            .join(ChatSession, ChatSession.id == ScreeningResult.session_id)
            .where(ScreeningResult.questionnaire == "asq")
            .where(ScreeningResult.interpretation.in_(
                ("non_acute_positive", "acute_positive"),
            ))
            .where(ScreeningResult.created_at >= cutoff)
            .order_by(desc(ScreeningResult.created_at))
            .limit(1)
        )

        # Фильтр по идентификатору. Если задан user_id — ищем сессии
        # этого пользователя; иначе — сессии конкретного guest_id.
        if user_id:
            stmt = stmt.where(ChatSession.user_id == user_id)
        else:
            stmt = stmt.where(ChatSession.guest_id == guest_id)

        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Frequency cap (Redis)
    # ------------------------------------------------------------------

    async def mark_offered(
        self,
        *,
        identifier: str,
        questionnaire: str,
    ) -> None:
        """Записать в Redis, что опросник был показан пользователю.

        identifier = user_id или guest_id (что есть на frontend'е).
        TTL = 7 дней.
        """
        if questionnaire not in VALID_QUESTIONNAIRES:
            raise ValueError(f"Unknown questionnaire: {questionnaire}")

        await self._redis.set(
            _offered_key(identifier, questionnaire),
            "1",
            ex=OFFERED_TTL_SECONDS,
        )

    async def was_recently_offered(
        self,
        *,
        identifier: str,
        questionnaire: str,
    ) -> bool:
        """Проверить, был ли опросник недавно предложен."""
        if questionnaire not in VALID_QUESTIONNAIRES:
            raise ValueError(f"Unknown questionnaire: {questionnaire}")

        exists = await self._redis.exists(
            _offered_key(identifier, questionnaire),
        )
        return bool(exists)

    # ------------------------------------------------------------------
    # История
    # ------------------------------------------------------------------

    async def get_history(
        self,
        *,
        user_id: str | None,
        guest_id: str | None,
        questionnaire: str | None = None,
        limit: int = 20,
    ) -> list[ScreeningResult]:
        """Получить историю прохождений (отсортированную desc по created_at).

        Args:
            user_id: id пользователя (или None).
            guest_id: id гостя (или None).
            questionnaire: фильтр по типу ('asq', 'pss4', 'osr') или None для всех.
            limit: максимум записей.

        Returns:
            Список ScreeningResult (может быть пустым).
        """
        if not user_id and not guest_id:
            return []

        stmt = (
            select(ScreeningResult)
            .join(ChatSession, ChatSession.id == ScreeningResult.session_id)
            .order_by(desc(ScreeningResult.created_at))
            .limit(limit)
        )

        if user_id:
            stmt = stmt.where(ChatSession.user_id == user_id)
        else:
            stmt = stmt.where(ChatSession.guest_id == guest_id)

        if questionnaire is not None:
            if questionnaire not in VALID_QUESTIONNAIRES:
                raise ValueError(f"Unknown questionnaire: {questionnaire}")
            stmt = stmt.where(ScreeningResult.questionnaire == questionnaire)

        result = await self._db.execute(stmt)
        return list(result.scalars().all())


# ============================================================================
# Module-level helper для PerceptionPipeline (hot-path)
# ============================================================================


async def has_active_asq_positive(
    db: AsyncSession,
    *,
    user_id: str | None,
    guest_id: str | None,
    within_days: int = ASQ_OVERRIDE_DAYS,
) -> bool:
    """Удобный хелпер для PerceptionPipeline без создания всего сервиса.

    Возвращает True если у user/guest есть положительный ASQ за последние
    `within_days` дней.

    Не использует Redis — работает только с БД (Redis нужен только сервису
    для frequency cap, не для override).
    """
    if not user_id and not guest_id:
        return False

    cutoff = datetime.now(timezone.utc) - timedelta(days=within_days)

    stmt = (
        select(ScreeningResult.id)
        .join(ChatSession, ChatSession.id == ScreeningResult.session_id)
        .where(ScreeningResult.questionnaire == "asq")
        .where(ScreeningResult.interpretation.in_(
            ("non_acute_positive", "acute_positive"),
        ))
        .where(ScreeningResult.created_at >= cutoff)
        .limit(1)
    )

    if user_id:
        stmt = stmt.where(ChatSession.user_id == user_id)
    else:
        stmt = stmt.where(ChatSession.guest_id == guest_id)

    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None
