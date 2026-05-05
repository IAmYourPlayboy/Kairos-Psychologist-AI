"""SQLAlchemy модели для досье пользователя.

Дизайн: §4 в spec (`docs/superpowers/specs/2026-05-02-perception-layer-design.md`).

3 таблицы:
- dossier_facts        — факт о пользователе (один уровень — один факт)
- dossier_quotes       — буквальные цитаты пользователя, связанные с фактом
- dossier_checkpoints  — где ReflectionAgent остановился для каждого user_id

Ключевое решение: **досье на user_id**, а не на session_id. Все факты
пользователя живут в одном пространстве, независимо от того, в каком чате
они были упомянуты. Поддерживает паттерн «один вечный чат».

Все ID — String(36) UUID для совместимости SQLite ↔ PostgreSQL.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.models import Base, _utcnow, _new_uuid


# ============================================================================
# Факты досье
# ============================================================================


class DossierFact(Base):
    """Один факт о пользователе.

    Хранится в папке/подпапке (см. core/perception/folders.py).
    Содержит summary (формулировку), tags (английский kebab-case),
    severity и confidence.

    Связан с цитатами (один-ко-многим) и опционально с superseded_by
    (если факт устарел и заменён новым — старый НЕ удаляется, версионируется).
    """

    __tablename__ = "dossier_facts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # Папка и подпапка (см. folders.py для допустимых значений)
    folder: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    subfolder: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Краткая формулировка факта от ReflectionAgent
    # Пример: "Папа пьёт, иногда поднимает руку"
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Список тэгов хранится как JSON (SQLite-совместимо).
    # Английский kebab-case: ["dad-aggression", "domestic-violence"]
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # 0.0-1.0 — насколько болезненно/опасно
    severity: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    # 0.0-1.0 — насколько ReflectionAgent уверен в факте
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    first_mentioned: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )
    last_mentioned: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )
    times_mentioned: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # ID сессий и сообщений, из которых факт извлечён (хранятся как JSON-массивы)
    source_session_ids: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list,
    )
    source_message_ids: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list,
    )

    # Если факт устарел и заменён — ссылка на новый.
    # Старые НЕ удаляем — версионируем для прозрачности и аудита.
    superseded_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("dossier_facts.id"), nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )

    # Связи
    quotes: Mapped[list[DossierQuote]] = relationship(
        "DossierQuote", back_populates="fact",
        cascade="all, delete-orphan",
        order_by="DossierQuote.created_at",
    )

    def __repr__(self) -> str:
        loc = self.folder if not self.subfolder else f"{self.folder}/{self.subfolder}"
        return (
            f"<DossierFact id={self.id[:8]} {loc} "
            f"sev={self.severity:.2f} '{self.summary[:30]}...'>"
        )


# ============================================================================
# Цитаты пользователя (доказательная база факта)
# ============================================================================


class DossierQuote(Base):
    """Буквальная цитата пользователя, на основании которой факт извлечён.

    Один факт может иметь несколько цитат (повторные упоминания → новые цитаты).
    Это даёт Кайросу возможность вернуться к точному тексту:
    «ты как-то писала: "бабушка опять про мою помаду..."»
    """

    __tablename__ = "dossier_quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    fact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("dossier_facts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id"), nullable=False,
    )
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("messages.id"), nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )

    # Связи
    fact: Mapped[DossierFact] = relationship(
        "DossierFact", back_populates="quotes",
    )

    def __repr__(self) -> str:
        return f"<DossierQuote fact={self.fact_id[:8]} '{self.text[:40]}...'>"


# ============================================================================
# Чекпойнт ReflectionAgent (один на пользователя)
# ============================================================================


class DossierCheckpoint(Base):
    """Закладка ReflectionAgent: где остановилась обработка.

    Один чекпойнт на user_id. При каждом успешном проходе агента
    last_processed_message_id сдвигается на самое последнее обработанное
    сообщение пользователя (по всем его сессиям).
    """

    __tablename__ = "dossier_checkpoints"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # NULL до первого прохода агента
    last_processed_message_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("messages.id"), nullable=True,
    )
    last_processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Счётчик для метрик в админке (Блок 30)
    facts_extracted_total: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<DossierCheckpoint user={self.user_id[:8]} "
            f"facts={self.facts_extracted_total}>"
        )
