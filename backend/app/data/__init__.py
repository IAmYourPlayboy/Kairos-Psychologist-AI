"""Модели данных, схемы и работа с БД (Блок 6a-6c)."""

from app.data.database import (
    async_session_factory,
    create_all_tables,
    dispose_engine,
    drop_all_tables,
    engine,
    get_db,
)
from app.data.models import (
    Base,
    ChatSession,
    FeedbackEvent,
    Message,
    ScreeningResult,
    Subscription,
    User,
)
from app.data.dossier_models import (
    DossierCheckpoint,
    DossierFact,
    DossierQuote,
)

__all__ = [
    # database
    "engine",
    "async_session_factory",
    "get_db",
    "dispose_engine",
    "create_all_tables",
    "drop_all_tables",
    # models — основа
    "Base",
    "User",
    "ChatSession",
    "Message",
    "FeedbackEvent",
    "Subscription",
    "ScreeningResult",
    # models — досье (Сессия 18+, слой восприятия)
    "DossierFact",
    "DossierQuote",
    "DossierCheckpoint",
]
