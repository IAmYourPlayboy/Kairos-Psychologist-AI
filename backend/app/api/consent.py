"""POST /api/consent — приём согласий пользователя на обработку ПДн.

ФЗ-152 ст.10: данные о психоэмоциональном состоянии — спецкатегория ПДн,
требует отдельного явного согласия. Это согласие должно быть:
- Явным (галочка, не молчаливое умолчание)
- Информированным (пользователь видел текст)
- Конкретным (не общая фраза «согласен на всё»)
- Отзываемым (клиент может удалить — DELETE /api/dossier уже это умеет)

Для аудита фиксируем:
- Время согласия (accepted_at)
- IP-адрес клиента
- User-Agent (браузер)
- Версия документа (если поменяем текст — пользователь увидит новую модалку)

Гость / зарегистрированный:
- guest_id обязателен пока пользователь не зарегистрирован
- При регистрации миграция guest → user_id (Блок 15)
- После регистрации — user_id (но guest_id тоже остаётся для истории)
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    ConsentRequest,
    ConsentResponse,
    ConsentStatus,
    ConsentStatusResponse,
)
from app.data.database import get_db
from app.data.models import UserConsent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consent", tags=["consent"])


# Какие типы согласий должны быть проставлены, чтобы пользователь мог писать боту
REQUIRED_CONSENTS: frozenset[str] = frozenset({
    "terms_of_service",
    "data_processing",
    "research_anonymized",
})


@router.post("", response_model=ConsentResponse)
async def submit_consents(
    payload: ConsentRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConsentResponse:
    """Записать согласия пользователя.

    Принимает массив согласий (обычно 3) и записывает каждое отдельной
    строкой в БД с временным штампом, IP и User-Agent.
    """
    if not payload.guest_id:
        # MVP: только гости. После Блока 13 (auth) добавим user_id из cookie.
        raise HTTPException(
            status_code=400,
            detail="guest_id is required (auth not implemented yet)",
        )

    ip = _client_ip(request)
    ua = request.headers.get("user-agent", "")[:500]  # truncate безопасно

    consent_ids: list[str] = []
    for item in payload.consents:
        consent = UserConsent(
            guest_id=payload.guest_id,
            consent_type=item.consent_type,
            document_version=item.document_version,
            ip_address=ip,
            user_agent=ua,
        )
        db.add(consent)
        await db.flush()  # чтобы получить consent.id
        consent_ids.append(consent.id)

    await db.commit()

    logger.info(
        "Consent: guest=%s accepted %d types (%s)",
        payload.guest_id[:8],
        len(consent_ids),
        ", ".join(c.consent_type for c in payload.consents),
    )

    return ConsentResponse(
        ok=True,
        accepted_count=len(consent_ids),
        consent_ids=consent_ids,
    )


@router.get("", response_model=ConsentStatusResponse)
async def get_consent_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    guest_id: str | None = None,
) -> ConsentStatusResponse:
    """Получить статус согласий.

    Возвращает список всех непустых согласий + флаг has_all_required —
    есть ли у пользователя все 3 обязательных согласия (не отозванных).
    """
    if not guest_id:
        return ConsentStatusResponse(consents=[], has_all_required=False)

    stmt = (
        select(UserConsent)
        .where(UserConsent.guest_id == guest_id)
        .order_by(UserConsent.accepted_at.desc())
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())

    consents = [
        ConsentStatus(
            consent_type=row.consent_type,  # type: ignore[arg-type]
            document_version=row.document_version,
            accepted_at=row.accepted_at.isoformat(),
            revoked_at=row.revoked_at.isoformat() if row.revoked_at else None,
        )
        for row in rows
    ]

    # Активные (не отозванные) согласия
    active_types = {
        c.consent_type
        for c in consents
        if c.revoked_at is None
    }
    has_all = REQUIRED_CONSENTS.issubset(active_types)

    return ConsentStatusResponse(
        consents=consents,
        has_all_required=has_all,
    )


def _client_ip(request: Request) -> str:
    """Извлечь IP клиента с учётом X-Forwarded-For (для прокси/CDN).

    Cloudflare/nginx ставит реальный IP в X-Forwarded-For; берём первый.
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # Берём первый IP из цепочки (это клиент)
        return xff.split(",")[0].strip()[:45]
    if request.client:
        return request.client.host[:45]
    return ""
