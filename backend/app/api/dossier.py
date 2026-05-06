"""GET / DELETE /api/dossier — просмотр и удаление досье пользователя.

ФЗ-152 «право на исправление и удаление»: каждый пользователь должен
иметь возможность увидеть всё, что сервис о нём знает, и удалить
любую часть или всё целиком.

MVP-авторизация: user_id или guest_id передаётся через query параметр.
Если задан guest_id — резолвим в user_id через привязанные chat_sessions.
После Блока 13 (auth) переключим на JWT через Depends(get_current_user).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.perception.dossier import DossierService
from app.data.database import get_db
from app.data.models import ChatSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dossier", tags=["dossier"])


# ============================================================================
# DTO для отдачи клиенту
# ============================================================================


class QuoteDTO(BaseModel):
    text: str
    created_at: str


class FactDTO(BaseModel):
    id: str
    folder: str
    subfolder: str | None
    summary: str
    tags: list[str]
    severity: float
    confidence: float
    times_mentioned: int
    first_mentioned: str
    last_mentioned: str
    superseded: bool
    quotes: list[QuoteDTO]


class DossierResponse(BaseModel):
    facts: list[FactDTO]


class DeleteResponse(BaseModel):
    ok: bool = True
    deleted_count: int = 0


# ============================================================================
# Резолвинг user_id из guest_id (MVP-хелпер)
# ============================================================================


async def _resolve_user_id(
    *,
    db: AsyncSession,
    user_id: str | None,
    guest_id: str | None,
) -> str | None:
    """Получить реальный user_id.

    - Если передан user_id — возвращаем как есть.
    - Если передан только guest_id — ищем chat_sessions с этим guest_id
      и возвращаем привязанный user_id (если он есть).
    - Иначе — None (UI должен показать «досье недоступно»).
    """
    if user_id:
        return user_id
    if not guest_id:
        return None

    # Ищем сессию с этим guest_id, у которой уже привязан user_id
    stmt = (
        select(ChatSession.user_id)
        .where(ChatSession.guest_id == guest_id)
        .where(ChatSession.user_id.is_not(None))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ============================================================================
# Endpoints
# ============================================================================


@router.get("", response_model=DossierResponse)
async def get_dossier(
    user_id: str | None = Query(
        None,
        description="ID пользователя (после Блока 13 — из JWT)",
    ),
    guest_id: str | None = Query(
        None,
        description=(
            "Гостевой ID. Используется на MVP до регистрации — "
            "резолвится в user_id через chat_sessions."
        ),
    ),
    db: AsyncSession = Depends(get_db),
) -> DossierResponse:
    """Вернуть все факты пользователя (включая superseded для прозрачности).

    Если user_id неизвестный или guest_id не привязан — возвращаем
    пустой список, не 404. UI отрисует «Кайрос ещё ничего не знает».
    """
    resolved_user_id = await _resolve_user_id(
        db=db, user_id=user_id, guest_id=guest_id,
    )
    if not resolved_user_id:
        return DossierResponse(facts=[])

    service = DossierService(db)
    facts = await service.all_user_facts(resolved_user_id)

    return DossierResponse(
        facts=[
            FactDTO(
                id=f.id,
                folder=f.folder,
                subfolder=f.subfolder,
                summary=f.summary,
                tags=f.tags,
                severity=f.severity,
                confidence=f.confidence,
                times_mentioned=f.times_mentioned,
                first_mentioned=f.first_mentioned.isoformat(),
                last_mentioned=f.last_mentioned.isoformat(),
                superseded=f.superseded_by is not None,
                quotes=[
                    QuoteDTO(text=q.text, created_at=q.created_at.isoformat())
                    for q in f.quotes
                ],
            )
            for f in facts
        ],
    )


@router.delete("/{fact_id}", response_model=DeleteResponse)
async def delete_fact(
    fact_id: str,
    user_id: str | None = Query(None),
    guest_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> DeleteResponse:
    """Удалить один факт пользователя.

    Returns:
        404 если факт не найден или принадлежит другому пользователю.
    """
    resolved_user_id = await _resolve_user_id(
        db=db, user_id=user_id, guest_id=guest_id,
    )
    if not resolved_user_id:
        raise HTTPException(
            status_code=404,
            detail="user_id или guest_id не определены",
        )

    service = DossierService(db)
    try:
        await service.delete_fact(
            user_id=resolved_user_id, fact_id=fact_id,
        )
        return DeleteResponse(ok=True, deleted_count=1)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("", response_model=DeleteResponse)
async def delete_all_dossier(
    user_id: str | None = Query(None),
    guest_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> DeleteResponse:
    """Удалить ВСЁ досье пользователя.

    Также сбрасывает чекпойнт ReflectionAgent — иначе после удаления
    агент бы решил «уже всё обработано» и не воссоздал факты заново
    из тех же сообщений.
    """
    resolved_user_id = await _resolve_user_id(
        db=db, user_id=user_id, guest_id=guest_id,
    )
    if not resolved_user_id:
        return DeleteResponse(ok=True, deleted_count=0)

    service = DossierService(db)
    count = await service.delete_all_for_user(resolved_user_id)
    logger.info(
        "Dossier wiped: user=%s count=%d", resolved_user_id[:8], count,
    )
    return DeleteResponse(ok=True, deleted_count=count)
