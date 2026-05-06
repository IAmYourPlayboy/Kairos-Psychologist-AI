"""SQLAlchemy модели данных Кайроса.

Архитектура: всё построено вокруг **data flywheel** — каждый диалог
анонимно записывается для последующего LoRA fine-tuning.

Таблицы:
- users               — зарегистрированные пользователи (опционально)
- chat_sessions       — одна сессия диалога (от первого сообщения до выхода)
- messages            — отдельные сообщения внутри сессии
- feedback_events     — обратная связь («помогло»/«не помогло»)
- subscriptions       — платные подписки (заполняется в Блоке 24)
- screening_results   — результаты опросников ASQ/PSS-4/ОСР (Блок 69)

Дизайн-решения:
- ID — String(36) для совместимости SQLite ↔ PostgreSQL.
  Генерируем `str(uuid4())` на клиенте или сервере.
- Все timestamp — `DateTime(timezone=True)`.
- Сообщения хранятся **уже анонимизированными** (анонимизация — Блок 6c).
- chat_sessions.user_id может быть NULL — это **гость** (анонимный пользователь).
  При регистрации все session.guest_id мигрируют → user_id (Блок 15).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ============================================================================
# Базовый класс для всех моделей
# ============================================================================


class Base(DeclarativeBase):
    """Общий базовый класс. От него наследуются все модели."""

    pass


def _utcnow() -> datetime:
    """Текущее время в UTC с таймзоной (для default-значений)."""
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    """Сгенерировать новый UUID-строку."""
    return str(uuid4())


# ============================================================================
# Пользователи (зарегистрированные)
# ============================================================================


class User(Base):
    """Зарегистрированный пользователь. Может иметь 0+ методов входа.

    Поля:
        id: UUID — первичный ключ
        created_at: дата регистрации
        display_name: псевдоним (необязательно)
        email / password_hash: для метода email+пароль
        telegram_id / vk_id / phone: для OAuth и SMS-логина
        is_verified: пройден ли скрининг подтверждения (email/SMS)
        subscription_tier: "free" | "support" | "twin"
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # OAuth и SMS
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    vk_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    subscription_tier: Mapped[str] = mapped_column(
        String(20), default="free", nullable=False
    )

    # Связи
    chat_sessions: Mapped[list[ChatSession]] = relationship(
        "ChatSession", back_populates="user", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list[Subscription]] = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} tier={self.subscription_tier}>"


# ============================================================================
# Сессии чата
# ============================================================================


class ChatSession(Base):
    """Одна сессия (от первого сообщения до выхода/завершения).

    Может принадлежать:
        - Зарегистрированному пользователю (user_id заполнен)
        - Гостю (guest_id заполнен, user_id = NULL)

    При регистрации гостя — все его сессии мигрируют через POST /api/sync/migrate
    (Блок 15): guest_id остаётся, user_id заполняется.
    """

    __tablename__ = "chat_sessions"

    # ID генерируется на КЛИЕНТЕ через crypto.randomUUID()
    # (см. CLAUDE.md → СИНХРОНИЗАЦИЯ).
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    guest_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Метрики сессии (для data flywheel)
    # Поле branch (rule-based селектор A/B) удалено в Сессии 18 —
    # теперь crisis_level определяется через PerceptionReport.
    crisis_level_max: Mapped[str] = mapped_column(
        String(20), default="normal", nullable=False
    )
    outcome: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # outcome: "improved" | "no_change" | "escalated" | "left"

    self_report_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    self_report_after: Mapped[int | None] = mapped_column(Integer, nullable=True)

    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Источник: пришло через чат (false) или через /api/sync (true)
    synced_from_client: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Связи
    user: Mapped[User | None] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[list[Message]] = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.server_timestamp",
    )
    feedback_events: Mapped[list[FeedbackEvent]] = relationship(
        "FeedbackEvent", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<ChatSession id={self.id} user={self.user_id or 'guest'} "
            f"branch={self.branch} crisis={self.crisis_level_max}>"
        )


# ============================================================================
# Сообщения
# ============================================================================


class Message(Base):
    """Одно сообщение в сессии. Текст УЖЕ анонимизирован перед записью.

    Анонимизация (Блок 6c):
        - ПДн (имена, телефоны, email, адреса) → заглушки
        - География → только регион
        - K-анонимность (k≥5) на этапе экспорта датасета.
    """

    __tablename__ = "messages"

    # ID генерируется на КЛИЕНТЕ
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id"), nullable=False, index=True
    )

    role: Mapped[str] = mapped_column(String(10), nullable=False)
    # role: "user" | "assistant" | "system"

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Время на клиенте
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    # Время прибытия на сервер (каноничный порядок)
    server_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )

    # NLP-метаданные (заполняются Блоком 12 — Aniemore)
    crisis_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    emotion_detected: Mapped[str | None] = mapped_column(String(30), nullable=True)
    distress_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Метрики LLM (только для role=assistant)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # JSON-сериализация PerceptionReport (логирование для data flywheel + LoRA).
    # Заполняется только когда use_perception_layer=True (Сессия 18+).
    # Для role=user — содержит отчёт анализатора об этом сообщении.
    perception_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Связи
    session: Mapped[ChatSession] = relationship(
        "ChatSession", back_populates="messages"
    )

    def __repr__(self) -> str:
        preview = self.content[:30].replace("\n", " ")
        return f"<Message id={self.id[:8]} role={self.role} '{preview}...'>"


# ============================================================================
# Обратная связь (data flywheel сигналы)
# ============================================================================


class FeedbackEvent(Base):
    """Сигнал для data flywheel: помогло или нет.

    Источники:
    - Явный (пользователь нажал кнопку «стало легче»)
    - Неявный (вышел молча, эскалация в кризис)
    """

    __tablename__ = "feedback_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    # Опциональная привязка к конкретному сообщению
    message_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("messages.id"), nullable=True
    )

    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # Типы:
    # "felt_better"       — пользователь нажал «стало легче»
    # "no_change"         — нажал «не изменилось»
    # "felt_worse"        — нажал «стало хуже»
    # "thumbs_up"         — лайкнул конкретное сообщение
    # "thumbs_down"       — дизлайкнул конкретное сообщение
    # "crisis_escalated"  — детектор поднял уровень кризиса
    # "session_timeout"   — пользователь молчит 10+ минут
    # "user_left"         — пользователь явно вышел

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    # Связи
    session: Mapped[ChatSession] = relationship(
        "ChatSession", back_populates="feedback_events"
    )

    def __repr__(self) -> str:
        return f"<FeedbackEvent {self.event_type} session={self.session_id[:8]}>"


# ============================================================================
# Подписки (Блок 24 — ЮKassa)
# ============================================================================


class Subscription(Base):
    """Платная подписка через ЮKassa.

    Заполняется в Блоке 24. Здесь — только структура.
    """

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )

    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    # tier: "support" (499₽) | "twin" (1999₽)

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    # status: "active" | "past_due" | "cancelled" | "expired"

    # Сохранённый метод оплаты для автосписания
    yookassa_payment_method_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    current_period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Цена в копейках (49900 = 499₽)
    price_kopecks: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    # Связи
    user: Mapped[User] = relationship("User", back_populates="subscriptions")

    def __repr__(self) -> str:
        return (
            f"<Subscription user={self.user_id[:8]} tier={self.tier} "
            f"status={self.status}>"
        )


# ============================================================================
# Результаты скрининга (Блок 69)
# ============================================================================


class ScreeningResult(Base):
    """Результат прохождения опросника (ASQ, PSS-4, ОСР).

    Заполняется в Блоке 69. Здесь — структура для модели данных.
    """

    __tablename__ = "screening_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id"), nullable=False, index=True
    )

    questionnaire: Mapped[str] = mapped_column(String(20), nullable=False)
    # "asq" | "pss4" | "osr"

    # Ответы в виде JSON-строки (чтобы работать на SQLite)
    raw_answers: Mapped[str] = mapped_column(Text, nullable=False)

    # Итоговая интерпретация
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    interpretation: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # ASQ: "positive" | "negative"
    # PSS-4: "low" | "moderate" | "high"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<ScreeningResult {self.questionnaire} "
            f"interp={self.interpretation} session={self.session_id[:8]}>"
        )
