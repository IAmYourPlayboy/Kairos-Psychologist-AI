"""Высокоуровневый CRUD над фактами и цитатами досье.

Этот модуль НЕ работает с LLM — он работает только с БД.
LLM-ориентированные операции (extract, classify, dedupe) живут в
ReflectionAgent (Фаза 5).

Дизайн: §4 в spec.
"""

from __future__ import annotations

from datetime import datetime, timezone
from math import exp
from typing import TypedDict
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.perception.folders import is_valid_subfolder
from app.data.dossier_models import (
    DossierCheckpoint,
    DossierFact,
    DossierQuote,
)


class QuoteInput(TypedDict):
    """Структура цитаты при создании / обновлении факта."""

    text: str
    session_id: str
    message_id: str


class DossierService:
    """Сервис над таблицами досье. Принимает AsyncSession в конструктор.

    Stateless относительно сервиса; всё состояние — в БД-сессии.
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    # ------------------------------------------------------------------
    # Создание / обновление
    # ------------------------------------------------------------------

    async def add_fact(
        self,
        *,
        user_id: str,
        folder: str,
        subfolder: str | None,
        summary: str,
        tags: list[str],
        severity: float,
        confidence: float,
        quotes: list[QuoteInput],
    ) -> DossierFact:
        """Создать новый факт с цитатами.

        Raises:
            ValueError: если папка/подпапка не валидны (см. folders.py).
        """
        if not is_valid_subfolder(folder, subfolder):
            raise ValueError(f"Invalid folder/subfolder: {folder}/{subfolder}")

        now = datetime.now(timezone.utc)
        fact = DossierFact(
            id=str(uuid4()),
            user_id=user_id,
            folder=folder,
            subfolder=subfolder,
            summary=summary,
            tags=tags,
            severity=severity,
            confidence=confidence,
            first_mentioned=now,
            last_mentioned=now,
            times_mentioned=max(1, len(quotes)),
            source_session_ids=list({q["session_id"] for q in quotes}),
            source_message_ids=[q["message_id"] for q in quotes],
        )
        self._db.add(fact)
        # Flush чтобы получить fact.id перед созданием цитат
        await self._db.flush()

        for q in quotes:
            quote = DossierQuote(
                id=str(uuid4()),
                fact_id=fact.id,
                text=q["text"],
                session_id=q["session_id"],
                message_id=q["message_id"],
            )
            self._db.add(quote)

        await self._db.commit()
        await self._db.refresh(fact, attribute_names=["quotes"])
        return fact

    async def update_fact_with_new_quote(
        self,
        *,
        fact_id: str,
        new_quote: QuoteInput,
        new_severity: float | None = None,
    ) -> DossierFact:
        """Добавить цитату к существующему факту, увеличить счётчик упоминаний.

        Если new_severity передан — берём максимум из старой и новой
        (severity монотонно растёт; если ситуация обостряется, мы это
        фиксируем, но не понижаем без явного решения).

        Raises:
            ValueError: если факт не найден.
        """
        fact = await self._db.get(DossierFact, fact_id)
        if fact is None:
            raise ValueError(f"Fact not found: {fact_id}")

        quote = DossierQuote(
            id=str(uuid4()),
            fact_id=fact.id,
            text=new_quote["text"],
            session_id=new_quote["session_id"],
            message_id=new_quote["message_id"],
        )
        self._db.add(quote)

        fact.times_mentioned += 1
        fact.last_mentioned = datetime.now(timezone.utc)
        if new_severity is not None:
            fact.severity = max(fact.severity, new_severity)

        # Дополним массивы источников
        if new_quote["session_id"] not in fact.source_session_ids:
            fact.source_session_ids = [
                *fact.source_session_ids,
                new_quote["session_id"],
            ]
        fact.source_message_ids = [
            *fact.source_message_ids,
            new_quote["message_id"],
        ]

        await self._db.commit()
        await self._db.refresh(fact, attribute_names=["quotes"])
        return fact

    async def supersede_fact(
        self,
        *,
        old_fact_id: str,
        new_fact_id: str,
    ) -> None:
        """Пометить старый факт как заменённый новым.

        Старый НЕ удаляется — только помечается. Это важно для аудита
        и для возможности «откатить» решение ReflectionAgent.

        Raises:
            ValueError: если старый факт не найден.
        """
        fact = await self._db.get(DossierFact, old_fact_id)
        if fact is None:
            raise ValueError(f"Fact not found: {old_fact_id}")
        fact.superseded_by = new_fact_id
        await self._db.commit()

    # ------------------------------------------------------------------
    # Чтение
    # ------------------------------------------------------------------

    async def get_facts_by_folders(
        self,
        user_id: str,
        *,
        folders: list[str] | None = None,
        include_superseded: bool = False,
    ) -> list[DossierFact]:
        """Получить факты пользователя.

        Args:
            user_id: id пользователя.
            folders: если задан — фильтр по списку верхнеуровневых папок.
            include_superseded: вернуть ли устаревшие (superseded_by != NULL).

        Returns:
            Список фактов с подгруженными цитатами.
        """
        stmt = (
            select(DossierFact)
            .where(DossierFact.user_id == user_id)
            .options(selectinload(DossierFact.quotes))
        )
        if folders:
            stmt = stmt.where(DossierFact.folder.in_(folders))
        if not include_superseded:
            stmt = stmt.where(DossierFact.superseded_by.is_(None))

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def top_relevant_facts(
        self,
        user_id: str,
        *,
        limit: int = 5,
    ) -> list[DossierFact]:
        """Топ-N самых релевантных фактов.

        Эвристика: severity * recency * confidence.
        recency = exp(-days_since_last_mention / 30). Угасает плавно:
        свежее упоминание = 1.0, через 30 дней ≈ 0.37, через 90 дней ≈ 0.05.

        Считаем в Python (не в SQL), потому что:
        - SQLite не имеет exp() из коробки.
        - На MVP пользователей мало → производительность не важна.
        - Когда понадобится — переедем на PostgreSQL и/или materialized view.
        """
        all_facts = await self.get_facts_by_folders(user_id)
        now = datetime.now(timezone.utc)

        def score(f: DossierFact) -> float:
            # SQLite не сохраняет таймзону → last_mentioned может вернуться
            # naive. Приводим к UTC-aware принудительно.
            last = f.last_mentioned
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            days = max(0.0, (now - last).total_seconds() / 86400.0)
            recency = exp(-days / 30.0)
            return f.severity * recency * f.confidence

        all_facts.sort(key=score, reverse=True)
        return all_facts[:limit]

    async def all_user_facts(self, user_id: str) -> list[DossierFact]:
        """ВСЕ факты пользователя (включая superseded).

        Используется в UI просмотра досье (Фаза 6) — там нужна полная
        прозрачность для пользователя.
        """
        return await self.get_facts_by_folders(
            user_id, include_superseded=True,
        )

    # ------------------------------------------------------------------
    # Удаление (для UI «удалить факт» / «удалить всё досье», Фаза 6)
    # ------------------------------------------------------------------

    async def delete_fact(self, *, user_id: str, fact_id: str) -> None:
        """Удалить факт пользователя. Цитаты убираются каскадом.

        Raises:
            ValueError: если факт не найден или принадлежит другому пользователю.
        """
        fact = await self._db.get(DossierFact, fact_id)
        if fact is None or fact.user_id != user_id:
            raise ValueError("Fact not found or doesn't belong to user")
        await self._db.delete(fact)
        await self._db.commit()

    async def delete_all_for_user(self, user_id: str) -> int:
        """Удалить ВСЁ досье пользователя.

        Также сбрасывает чекпойнт ReflectionAgent — иначе при следующем
        запуске агент решит, что уже всё обработано, и не воссоздаст
        факты из старых сообщений.

        Returns:
            Количество удалённых фактов.
        """
        facts = await self.get_facts_by_folders(
            user_id, include_superseded=True,
        )
        count = len(facts)
        for f in facts:
            await self._db.delete(f)
        # Также сбрасываем чекпойнт
        cp = await self._db.get(DossierCheckpoint, user_id)
        if cp:
            await self._db.delete(cp)
        await self._db.commit()
        return count

    # ------------------------------------------------------------------
    # Чекпойнт
    # ------------------------------------------------------------------

    async def get_checkpoint(self, user_id: str) -> DossierCheckpoint | None:
        """Вернуть чекпойнт ReflectionAgent для пользователя или None."""
        return await self._db.get(DossierCheckpoint, user_id)

    async def update_checkpoint(
        self,
        *,
        user_id: str,
        last_processed_message_id: str,
        facts_extracted: int,
    ) -> DossierCheckpoint:
        """Создать или обновить чекпойнт.

        facts_extracted_total — накапливающийся счётчик (для метрик).
        last_processed_message_id — указатель «обработано до сюда».
        """
        cp = await self._db.get(DossierCheckpoint, user_id)
        now = datetime.now(timezone.utc)
        if cp is None:
            cp = DossierCheckpoint(
                user_id=user_id,
                last_processed_message_id=last_processed_message_id,
                last_processed_at=now,
                facts_extracted_total=facts_extracted,
                created_at=now,
                updated_at=now,
            )
            self._db.add(cp)
        else:
            cp.last_processed_message_id = last_processed_message_id
            cp.last_processed_at = now
            cp.facts_extracted_total += facts_extracted
            cp.updated_at = now
        await self._db.commit()
        await self._db.refresh(cp)
        return cp
