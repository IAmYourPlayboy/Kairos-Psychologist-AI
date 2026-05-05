"""Pydantic-схемы для API запросов и ответов.

Зачем отдельный файл: разделить «бизнес-логику» (модели SQLAlchemy в data/)
от «контракта API» (схемы запросов/ответов здесь).

Изменения схем — это ломающие изменения для клиентов, поэтому держим их
в одном месте и версионируем.
"""

from typing import Literal

from pydantic import BaseModel, Field


# ============================================================================
# Чат
# ============================================================================


class ChatMessageHistory(BaseModel):
    """Одно сообщение в истории диалога (как клиент шлёт нам)."""

    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=10_000)


class ChatRequest(BaseModel):
    """Запрос к POST /api/chat.

    Клиент шлёт текущее сообщение + опциональный контекст сессии и истории.
    """

    message: str = Field(
        ..., min_length=1, max_length=10_000, description="Текст сообщения пользователя"
    )

    # Идентификатор сессии — генерируется на клиенте через crypto.randomUUID().
    # Если не передан — сервер создаст новую сессию.
    session_id: str | None = Field(
        default=None,
        description="UUID сессии. Если не задан — будет создан новый.",
    )

    # Идентификатор гостя (хранится в localStorage до регистрации).
    # Когда клиент зарегистрируется — все его сессии мигрируют через /api/sync/migrate.
    guest_id: str | None = Field(
        default=None, description="UUID гостя (для анонимных пользователей)"
    )

    # Возрастная группа пользователя — для подбора кризисных контактов.
    age_group: Literal["child", "youth", "adult"] | None = Field(
        default="adult",
        description="Возрастная группа: child (<18), youth (<25), adult (25+)",
    )

    # История последних сообщений — клиент шлёт чтобы LLM имел контекст.
    # Ограничиваем 50 последними сообщениями чтобы не взорвать контекст LLM.
    history: list[ChatMessageHistory] = Field(
        default_factory=list,
        max_length=50,
        description="История последних сообщений диалога (без текущего)",
    )


class CrisisContactDTO(BaseModel):
    """Кризисный контакт для отдачи клиенту."""

    name: str
    phone: str
    description: str


class ChatResponse(BaseModel):
    """Ответ от POST /api/chat."""

    reply: str = Field(..., description="Ответ бота")

    session_id: str = Field(
        ..., description="UUID сессии (новый или переданный клиентом)"
    )

    # ID сообщения бота — клиент использует для feedback (Блок 5.5)
    message_id: str = Field(..., description="UUID сохранённого сообщения бота")

    crisis_level: Literal["normal", "elevated", "high", "immediate"] = Field(
        ..., description="Уровень кризиса по детектору"
    )

    # Контакты возвращаем только если crisis_level != normal
    crisis_contacts: list[CrisisContactDTO] = Field(
        default_factory=list,
        description="Кризисные контакты (пустой список если кризиса нет)",
    )

    branch: Literal["A", "B"] | None = Field(
        default=None, description="Выбранная ветка протокола: A=мобилизация, B=стабилизация"
    )

    # Метрики LLM (для отладки и аналитики)
    response_time_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    # Если был fallback из-за ошибки LLM — диагностический текст для отладки
    # (показывается только в режиме debug=true)
    llm_error: str | None = None


# ============================================================================
# Feedback (Блок 5.5)
# ============================================================================


FeedbackEventType = Literal[
    "felt_better",
    "no_change",
    "felt_worse",
    "thumbs_up",
    "thumbs_down",
    "crisis_escalated",
    "session_timeout",
    "user_left",
]


class FeedbackRequest(BaseModel):
    """Запрос к POST /api/feedback."""

    session_id: str
    message_id: str | None = None
    event_type: FeedbackEventType


class FeedbackResponse(BaseModel):
    """Ответ от POST /api/feedback."""

    ok: bool = True
    feedback_id: str
