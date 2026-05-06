"""GET / DELETE /api/dossier — просмотр и удаление досье пользователя.

ФЗ-152 «право на исправление и удаление»: каждый пользователь должен
иметь возможность увидеть всё, что сервис о нём знает, и удалить
любую часть или всё целиком.

MVP-авторизация: user_id передаётся через query параметр (заглушка).
После Блока 13 (auth) переключим на JWT через Depends(get_current_user).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.perception.dossier import DossierService
from app.data.database import get_db

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
# Endpoints
# ============================================================================


@router.get("", response_model=DossierResponse)
async def get_dossier(
    user_id: str = Query(
        ...,
        description="ID пользователя (после Блока 13 — из JWT)",
    ),
    db: AsyncSession = Depends(get_db),
) -> DossierResponse:
    """Вернуть все факты пользователя (включая superseded для прозрачности).

    Если user_id неизвестный — возвращаем пустой список, не 404.
    Это упрощает UI: первый заход показывает «Кайрос ещё ничего не знает»,
    а не страницу с ошибкой.
    """
    service = DossierService(db)
    facts = await service.all_user_facts(user_id)

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
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> DeleteResponse:
    """Удалить один факт пользователя.

    Returns:
        404 если факт не найден или принадлежит другому пользователю.
    """
    service = DossierService(db)
    try:
        await service.delete_fact(user_id=user_id, fact_id=fact_id)
        return DeleteResponse(ok=True, deleted_count=1)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("", response_model=DeleteResponse)
async def delete_all_dossier(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> DeleteResponse:
    """Удалить ВСЁ досье пользователя.

    Также сбрасывает чекпойнт ReflectionAgent — иначе после удаления
    агент бы решил «уже всё обработано» и не воссоздал факты заново
    из тех же сообщений.
    """
    service = DossierService(db)
    count = await service.delete_all_for_user(user_id)
    logger.info(
        "Dossier wiped: user=%s count=%d", user_id[:8], count,
    )
    return DeleteResponse(ok=True, deleted_count=count)
