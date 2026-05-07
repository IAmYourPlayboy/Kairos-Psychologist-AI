"""GET/PATCH/DELETE /api/sessions — управление сессиями пользователя.

Только для залогиненных. Гости работают с сессиями локально через Dexie.

Эндпоинты:
- GET    /api/sessions               — список сессий текущего пользователя
- GET    /api/sessions/{id}          — одна сессия + сообщения
- PATCH  /api/sessions/{id}          — переименовать (title)
- DELETE /api/sessions/{id}          — удалить сессию (каскадом сообщения и feedback)
- POST   /api/sessions/migrate       — мигрировать guest_id → текущий user_id

Ответ ChatSession содержит:
- id, created_at, ended_at, message_count, duration_seconds
- crisis_level_max, outcome
- title (вычисляется как первое user-сообщение, обрезанное до 50 симв)
- last_message_at — server_timestamp последнего сообщения
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user
from app.data.database import get_db
from app.data.dossier_models import DossierCheckpoint, DossierFact
from app.data.models import ChatSession, Message, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


# ============================================================================
# Схемы
# ============================================================================


class SessionSummary(BaseModel):
    """Краткое описание сессии для списка."""

    id: str
    created_at: str
    ended_at: str | None
    message_count: int
    crisis_level_max: str
    outcome: str | None
    duration_seconds: int | None
    title: str
    last_message_at: str | None


class SessionListResponse(BaseModel):
    sessions: list[SessionSummary]


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    crisis_level: str | None


class SessionDetailResponse(BaseModel):
    session: SessionSummary
    messages: list[MessageItem]


class RenameSessionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class MigrateRequest(BaseModel):
    """Запрос на миграцию гостевых данных в текущий аккаунт."""

    guest_id: str


class MigrateResponse(BaseModel):
    ok: bool = True
    sessions_migrated: int
    facts_migrated: int


# ============================================================================
# GET /api/sessions
# ============================================================================


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionListResponse:
    """Вернуть все сессии текущего пользователя.

    Сортировка: сначала самые свежие (по last_message_at, затем created_at).
    """
    # JOIN: ChatSession + последнее сообщение (для last_message_at и title)
    # Берём в один запрос — иначе O(N) запросов на N сессий.
    last_msg_subq = (
        select(
            Message.session_id,
            func.max(Message.server_timestamp).label("last_at"),
        )
        .group_by(Message.session_id)
        .subquery()
    )

    stmt = (
        select(ChatSession, last_msg_subq.c.last_at)
        .outerjoin(last_msg_subq, ChatSession.id == last_msg_subq.c.session_id)
        .where(ChatSession.user_id == user.id)
        .order_by(desc(last_msg_subq.c.last_at), desc(ChatSession.created_at))
    )
    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return SessionListResponse(sessions=[])

    # Для title — достаём первое user-сообщение каждой сессии в один запрос
    session_ids = [s.id for s, _ in rows]
    first_user_msg_stmt = (
        select(
            Message.session_id,
            func.min(Message.server_timestamp).label("first_ts"),
        )
        .where(Message.session_id.in_(session_ids))
        .where(Message.role == "user")
        .group_by(Message.session_id)
        .subquery()
    )
    first_user_msgs = (
        select(Message)
        .join(
            first_user_msg_stmt,
            (Message.session_id == first_user_msg_stmt.c.session_id)
            & (Message.server_timestamp == first_user_msg_stmt.c.first_ts),
        )
    )
    first_user_result = await db.execute(first_user_msgs)
    first_msg_by_session = {m.session_id: m for m in first_user_result.scalars()}

    sessions = [
        _build_summary(
            session=s,
            last_at=last_at,
            first_user_message=first_msg_by_session.get(s.id),
        )
        for s, last_at in rows
    ]
    return SessionListResponse(sessions=sessions)


# ============================================================================
# GET /api/sessions/{id}
# ============================================================================


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionDetailResponse:
    """Получить одну сессию + все её сообщения.

    Только если сессия принадлежит этому пользователю. Иначе 404
    (не 403, чтобы не утекало существование чужих сессий).
    """
    session = await db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    msgs_stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.server_timestamp.asc())
    )
    msgs_result = await db.execute(msgs_stmt)
    messages = list(msgs_result.scalars().all())

    first_user_msg = next((m for m in messages if m.role == "user"), None)
    last_at = max(
        (m.server_timestamp for m in messages),
        default=None,
    )

    summary = _build_summary(
        session=session,
        last_at=last_at,
        first_user_message=first_user_msg,
    )

    return SessionDetailResponse(
        session=summary,
        messages=[
            MessageItem(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.server_timestamp.isoformat(),
                crisis_level=m.crisis_level,
            )
            for m in messages
        ],
    )


# ============================================================================
# PATCH /api/sessions/{id}
# ============================================================================


@router.patch("/{session_id}")
async def rename_session(
    session_id: str,
    payload: RenameSessionRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """Переименовать сессию.

    Сейчас в модели нет поля title — только в Dexie. Это endpoint-заглушка
    для будущего, когда добавим `ChatSession.title`. На MVP — возвращаем 501.
    """
    session = await db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    # TODO: добавить ChatSession.title (миграция) и сохранять.
    # Пока — клиент держит title в Dexie локально.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Server-side titles not implemented yet",
    )


# ============================================================================
# DELETE /api/sessions/{id}
# ============================================================================


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, bool]:
    """Удалить сессию (каскадом — сообщения и feedback)."""
    session = await db.get(ChatSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    await db.delete(session)
    await db.commit()
    logger.info("Session deleted: id=%s user=%s", session_id[:8], user.id[:8])
    return {"ok": True}


# ============================================================================
# POST /api/sessions/migrate
# ============================================================================


@router.post("/migrate", response_model=MigrateResponse)
async def migrate_guest(
    payload: MigrateRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MigrateResponse:
    """Привязать гостевые сессии и досье к текущему пользователю.

    Используется когда:
    - Пользователь зарегистрировался отдельно от гостевой сессии
      (например, через VK/Telegram/SMS на этапе выбора метода входа)
    - Залогинился на устройстве, где раньше работал как гость

    Идемпотентно: повторный вызов с тем же guest_id ничего не сломает
    (просто найдёт 0 сессий для миграции).
    """
    guest_id = payload.guest_id

    # ChatSession: гостевые → user_id
    sessions = await db.execute(
        select(ChatSession).where(
            (ChatSession.guest_id == guest_id)
            & (ChatSession.user_id.is_(None)),
        ),
    )
    sessions_migrated = 0
    for session in sessions.scalars().all():
        session.user_id = user.id
        sessions_migrated += 1

    # DossierFact: на гостевом MVP user_id у факта мог быть guest_id'ом
    facts = await db.execute(
        select(DossierFact).where(DossierFact.user_id == guest_id),
    )
    facts_migrated = 0
    for fact in facts.scalars().all():
        fact.user_id = user.id
        facts_migrated += 1

    # DossierCheckpoint
    checkpoints = await db.execute(
        select(DossierCheckpoint).where(
            DossierCheckpoint.user_id == guest_id,
        ),
    )
    for cp in checkpoints.scalars().all():
        cp.user_id = user.id

    await db.commit()
    logger.info(
        "Manual migrate: guest=%s → user=%s, sessions=%d facts=%d",
        guest_id[:8], user.id[:8], sessions_migrated, facts_migrated,
    )
    return MigrateResponse(
        sessions_migrated=sessions_migrated,
        facts_migrated=facts_migrated,
    )


# ============================================================================
# Внутренние хелперы
# ============================================================================


def _build_summary(
    *,
    session: ChatSession,
    last_at,
    first_user_message: Message | None,
) -> SessionSummary:
    """Собрать SessionSummary из ChatSession + last_message_timestamp."""
    title = "Новая беседа"
    if first_user_message:
        # Обрезаем до 50 символов, убираем переводы строк
        text = first_user_message.content.replace("\n", " ").strip()
        title = text[:50] + ("…" if len(text) > 50 else "")

    return SessionSummary(
        id=session.id,
        created_at=session.created_at.isoformat(),
        ended_at=session.ended_at.isoformat() if session.ended_at else None,
        message_count=session.message_count,
        crisis_level_max=session.crisis_level_max,
        outcome=session.outcome,
        duration_seconds=session.duration_seconds,
        title=title,
        last_message_at=last_at.isoformat() if last_at else None,
    )
