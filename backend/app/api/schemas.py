"""Pydantic-схемы для API запросов и ответов.

Зачем отдельный файл: разделить «бизнес-логику» (модели SQLAlchemy в data/)
от «контракта API» (схемы запросов/ответов здесь).

Изменения схем — это ломающие изменения для клиентов, поэтому держим их
в одном месте и версионируем.
"""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


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


# ============================================================================
# Consent (Блок B3, ФЗ-152)
# ============================================================================


ConsentType = Literal[
    "terms_of_service",     # Пользовательское соглашение
    "data_processing",      # Обработка данных о состоянии (ст.10 ФЗ-152)
    "research_anonymized",  # Сбор обезличенных данных для исследований
]


class ConsentItem(BaseModel):
    """Одно согласие в запросе."""

    consent_type: ConsentType
    document_version: str = Field(default="1.0", max_length=20)


class ConsentRequest(BaseModel):
    """Запрос к POST /api/consent.

    Клиент шлёт ВСЕ 3 согласия одним пакетом (с фронта три чекбокса нельзя
    submit-нуть пока не отмечены все).
    """

    guest_id: str | None = Field(
        default=None,
        description="UUID гостя. Один из guest_id/user_id обязателен.",
    )
    consents: list[ConsentItem] = Field(..., min_length=1, max_length=10)


class ConsentResponse(BaseModel):
    """Ответ от POST /api/consent."""

    ok: bool = True
    accepted_count: int
    consent_ids: list[str]


class ConsentStatus(BaseModel):
    """Запись статуса согласия (для GET /api/consent)."""

    consent_type: ConsentType
    document_version: str
    accepted_at: str  # ISO 8601
    revoked_at: str | None = None


class ConsentStatusResponse(BaseModel):
    """Ответ от GET /api/consent."""

    consents: list[ConsentStatus]
    has_all_required: bool  # все 3 типа приняты и не отозваны


# ============================================================================
# Auth (Блок C1)
# ============================================================================


class RegisterRequest(BaseModel):
    """Запрос к POST /api/auth/register."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)

    # guest_id — если регистрируется бывший гость, миграция его сессий и досье.
    # Опциональный: если зашли прямо на /auth/register, его не будет.
    guest_id: str | None = None

    # Согласия — обязательны при регистрации.
    # Если у guest_id уже есть consent в БД, можно отправить пустой массив.
    # Иначе — три типа должны быть приняты, иначе 400.
    consents: list[ConsentItem] = Field(default_factory=list, max_length=10)


class LoginRequest(BaseModel):
    """Запрос к POST /api/auth/login."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class UserResponse(BaseModel):
    """Публичная информация о пользователе.

    НЕ включает password_hash, telegram_id, vk_id, phone — только то, что
    клиент имеет право видеть про себя.
    """

    id: str
    email: str | None
    display_name: str | None
    subscription_tier: str
    is_verified: bool
    created_at: str  # ISO 8601
    # Soft-delete статус: если задан — пользователь нажал «удалить аккаунт»
    # и в течение этого времени может отменить через POST /me/cancel-deletion.
    # Frontend по этому полю показывает баннер «удаление через X дней».
    deletion_scheduled_at: str | None = None


class AuthResponse(BaseModel):
    """Ответ от register / login / refresh.

    Сами токены НЕ возвращаются в теле — они в httpOnly cookies.
    Возвращаем только данные пользователя.
    """

    ok: bool = True
    user: UserResponse


class RefreshRequest(BaseModel):
    """Запрос к POST /api/auth/refresh.

    Тело пустое — refresh-токен берётся из httpOnly cookie.
    Класс существует только чтобы FastAPI не требовал тело при tests
    через httpx с пустым body.
    """

    pass


class LogoutRequest(BaseModel):
    """Запрос к POST /api/auth/logout."""

    # Если True — отзывает ВСЕ refresh-токены пользователя (logout со всех
    # устройств). По умолчанию — только текущий refresh.
    everywhere: bool = False
