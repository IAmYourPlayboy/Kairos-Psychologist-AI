"""Эндпоинты для валидированных опросников ASQ и PSS-4.

Структура:
- GET  /api/screening/asq            — структура опросника (вопросы)
- GET  /api/screening/pss4           — структура опросника (вопросы)
- POST /api/screening/asq            — отправка ответов ASQ
- POST /api/screening/pss4           — отправка ответов PSS-4
- GET  /api/screening/history        — история прохождений (по session_id или из JWT)
- POST /api/screening/mark-offered   — frontend сообщил «опросник был показан»
- GET  /api/screening/should-offer   — bool «можно показывать опросник?»

ADR-1: ASQ-positive override risk_level=immediate в течение 7 дней —
       реализуется в PerceptionPipeline через has_active_asq_positive().
       Здесь просто сохраняем результат; override срабатывает на следующих
       вызовах /api/chat.

ADR-3: frequency cap через Redis (TTL 7 дней).

ADR-5: query'и принимают и user_id (из JWT), и guest_id (из query/body).
"""

from __future__ import annotations

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_optional_user
from app.core.perception.redis_client import get_redis
from app.core.screening import (
    ASQ,
    PSS4,
    ScreeningService,
)
from app.core.screening.asq import ASQAnswer
from app.data.database import get_db
from app.data.models import ChatSession, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/screening", tags=["screening"])


# ============================================================================
# DTO для отдачи структуры опросников
# ============================================================================


class ASQQuestionDTO(BaseModel):
    id: int
    text: str
    is_acuity: bool


class PSS4QuestionDTO(BaseModel):
    id: int
    text: str
    reverse: bool


class ASQQuestionnaireResponse(BaseModel):
    """Структура опросника ASQ для отображения на frontend'е."""

    questionnaire: Literal["asq"] = "asq"
    questions: list[ASQQuestionDTO]
    answer_options: list[Literal["yes", "no", "decline"]] = ["yes", "no", "decline"]


class PSS4QuestionnaireResponse(BaseModel):
    """Структура опросника PSS-4."""

    questionnaire: Literal["pss4"] = "pss4"
    questions: list[PSS4QuestionDTO]
    # Подсказки шкалы для UI (0..4). reverse-инверсия делается на бекенде.
    scale: dict[int, str] = Field(
        default_factory=lambda: {
            0: "никогда",
            1: "почти никогда",
            2: "иногда",
            3: "довольно часто",
            4: "очень часто",
        },
    )


# ============================================================================
# DTO для приёма ответов и отдачи результата
# ============================================================================


class ASQSubmitRequest(BaseModel):
    """Тело POST /api/screening/asq.

    answers: словарь {qid: "yes"|"no"|"decline"}. Ключи приходят как строки
    из JSON, конвертируем в int при обработке.
    """

    session_id: str = Field(..., min_length=1, max_length=64)
    answers: dict[str, ASQAnswer] = Field(..., min_length=1, max_length=10)


class PSS4SubmitRequest(BaseModel):
    """Тело POST /api/screening/pss4."""

    session_id: str = Field(..., min_length=1, max_length=64)
    answers: dict[str, int] = Field(..., min_length=1, max_length=10)


class ASQSubmitResponse(BaseModel):
    """Ответ POST /api/screening/asq."""

    interpretation: Literal["negative", "non_acute_positive", "acute_positive"]
    score: int
    is_positive: bool
    record_id: str


class PSS4SubmitResponse(BaseModel):
    """Ответ POST /api/screening/pss4."""

    interpretation: Literal["low", "moderate", "high"]
    score: int
    record_id: str


# ============================================================================
# DTO для истории
# ============================================================================


class ScreeningHistoryItem(BaseModel):
    id: str
    questionnaire: Literal["asq", "pss4", "osr"]
    score: float | None
    interpretation: str | None
    created_at: str  # ISO 8601


class ScreeningHistoryResponse(BaseModel):
    items: list[ScreeningHistoryItem]


# ============================================================================
# DTO для frequency cap
# ============================================================================


class MarkOfferedRequest(BaseModel):
    identifier: str = Field(..., min_length=1, max_length=64)
    questionnaire: Literal["asq", "pss4", "osr"]


class MarkOfferedResponse(BaseModel):
    ok: bool = True


class ShouldOfferResponse(BaseModel):
    """Ответ GET /api/screening/should-offer.

    should_offer = True если опросник НЕ предлагался в последние 7 дней.
    """

    should_offer: bool


# ============================================================================
# Helpers
# ============================================================================


async def _resolve_session(
    db: AsyncSession, session_id: str,
) -> ChatSession:
    """Найти существующую сессию или вернуть 404.

    Скрининг привязан к сессии (через FK), поэтому сессия должна быть
    создана раньше — например, первым сообщением в чате.
    """
    session = await db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ChatSession not found: {session_id}",
        )
    return session


# ============================================================================
# Эндпоинты — структура опросников
# ============================================================================


@router.get("/asq", response_model=ASQQuestionnaireResponse)
async def get_asq_questionnaire() -> ASQQuestionnaireResponse:
    """Вернуть структуру ASQ для отображения на frontend'е.

    5-й (acuity) вопрос отдаётся вместе с остальными, но frontend должен
    показывать его ТОЛЬКО если на 1–4 был хотя бы один "yes".
    """
    return ASQQuestionnaireResponse(
        questions=[
            ASQQuestionDTO(id=q.id, text=q.text, is_acuity=q.is_acuity)
            for q in ASQ
        ],
    )


@router.get("/pss4", response_model=PSS4QuestionnaireResponse)
async def get_pss4_questionnaire() -> PSS4QuestionnaireResponse:
    """Вернуть структуру PSS-4 для отображения."""
    return PSS4QuestionnaireResponse(
        questions=[
            PSS4QuestionDTO(id=q.id, text=q.text, reverse=q.reverse)
            for q in PSS4
        ],
    )


# ============================================================================
# Эндпоинты — приём ответов
# ============================================================================


@router.post("/asq", response_model=ASQSubmitResponse)
async def submit_asq(
    payload: ASQSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ASQSubmitResponse:
    """Принять ответы ASQ, посчитать, сохранить.

    Если результат positive (non_acute или acute) — он автоматически
    активирует override risk_level=immediate в следующих вызовах /api/chat
    (через has_active_asq_positive()).
    """
    session = await _resolve_session(db, payload.session_id)

    # Конвертируем ключи строк → int (JSON object keys всегда строки)
    try:
        answers_int = {int(k): v for k, v in payload.answers.items()}
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid question id (must be int): {e}",
        )

    service = ScreeningService(db, get_redis())
    try:
        result, record = await service.save_asq(
            session_id=session.id, answers=answers_int,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        )

    return ASQSubmitResponse(
        interpretation=result.interpretation,
        score=result.score,
        is_positive=result.is_positive,
        record_id=record.id,
    )


@router.post("/pss4", response_model=PSS4SubmitResponse)
async def submit_pss4(
    payload: PSS4SubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PSS4SubmitResponse:
    """Принять ответы PSS-4, посчитать, сохранить.

    PSS-4 НЕ влияет на risk_level — он только информирует терапевтическую
    маршрутизацию (выбор техник, тон бота).
    """
    session = await _resolve_session(db, payload.session_id)

    try:
        answers_int = {int(k): v for k, v in payload.answers.items()}
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid question id (must be int): {e}",
        )

    service = ScreeningService(db, get_redis())
    try:
        result, record = await service.save_pss4(
            session_id=session.id, answers=answers_int,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        )

    return PSS4SubmitResponse(
        interpretation=result.interpretation,
        score=result.score,
        record_id=record.id,
    )


# ============================================================================
# Эндпоинты — история
# ============================================================================


@router.get("/history", response_model=ScreeningHistoryResponse)
async def get_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    session_id: Annotated[str | None, Query(
        description=(
            "ID сессии (для гостей). Резолвим guest_id через ChatSession."
        ),
    )] = None,
    questionnaire: Annotated[Literal["asq", "pss4", "osr"] | None, Query(
        description="Фильтр по типу опросника",
    )] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ScreeningHistoryResponse:
    """Вернуть историю прохождений опросников.

    Резолвинг идентификатора:
    - Если есть JWT (current_user) — берём user_id оттуда.
    - Иначе — пытаемся резолвить guest_id из переданной session_id.
    - Если ни того, ни другого — вернём пустой список (а не 401), чтобы
      UI отобразил «история пуста» вместо ошибки.
    """
    user_id: str | None = current_user.id if current_user else None
    guest_id: str | None = None

    if not user_id and session_id:
        # Достанем guest_id из ChatSession
        stmt = select(ChatSession.guest_id).where(ChatSession.id == session_id)
        guest_id = (await db.execute(stmt)).scalar_one_or_none()

    if not user_id and not guest_id:
        return ScreeningHistoryResponse(items=[])

    service = ScreeningService(db, get_redis())
    records = await service.get_history(
        user_id=user_id,
        guest_id=guest_id,
        questionnaire=questionnaire,
        limit=limit,
    )

    return ScreeningHistoryResponse(
        items=[
            ScreeningHistoryItem(
                id=r.id,
                questionnaire=r.questionnaire,  # type: ignore[arg-type]
                score=r.score,
                interpretation=r.interpretation,
                created_at=r.created_at.isoformat(),
            )
            for r in records
        ],
    )


# ============================================================================
# Эндпоинты — frequency cap
# ============================================================================


@router.post("/mark-offered", response_model=MarkOfferedResponse)
async def mark_offered(
    payload: MarkOfferedRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MarkOfferedResponse:
    """Frontend сообщает: «я показал этот опросник пользователю».

    Не предлагать его повторно в течение 7 дней.
    """
    service = ScreeningService(db, get_redis())
    try:
        await service.mark_offered(
            identifier=payload.identifier,
            questionnaire=payload.questionnaire,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return MarkOfferedResponse(ok=True)


@router.get("/should-offer", response_model=ShouldOfferResponse)
async def should_offer(
    db: Annotated[AsyncSession, Depends(get_db)],
    identifier: Annotated[str, Query(min_length=1, max_length=64)],
    questionnaire: Annotated[Literal["asq", "pss4", "osr"], Query()],
) -> ShouldOfferResponse:
    """Можно ли сейчас показать опросник этому пользователю?

    Возвращает True если в последние 7 дней флаг НЕ ставился.
    """
    service = ScreeningService(db, get_redis())
    try:
        recently = await service.was_recently_offered(
            identifier=identifier,
            questionnaire=questionnaire,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return ShouldOfferResponse(should_offer=not recently)
