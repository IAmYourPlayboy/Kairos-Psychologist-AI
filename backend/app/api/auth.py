"""POST /api/auth/* — регистрация, логин, обновление токена, выход.

Архитектура:
- POST /register — создать User, выдать access+refresh JWT, опционально
  мигрировать guest сессии и досье.
- POST /login — проверить email+пароль, выдать access+refresh JWT.
- POST /refresh — обновить access по refresh (с rotation: старый revoke,
  новый выдать).
- POST /logout — отозвать refresh (текущий или все), очистить cookies.
- GET /me — вернуть данные текущего пользователя.

Безопасность:
- Пароли хешируются через Argon2id (см. password.py).
- Токены в httpOnly cookies (см. cookies.py).
- Refresh-токены хранятся в БД (хешем) для возможности отзыва.
- Refresh rotation с burn-on-replay (см. tokens.py).
- Constant-time проверка пароля (внутри pwdlib).
- Time-uniform ответ при «нет такого юзера» vs «неправильный пароль» —
  оба возвращают 401 без деталей.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.consent import REQUIRED_CONSENTS
from app.api.schemas import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    UserResponse,
)
from app.core.auth.account_deletion import (
    cancel_account_deletion,
    schedule_account_deletion,
)
from app.core.auth.cookies import (
    REFRESH_COOKIE_NAME,
    clear_auth_cookies,
    set_auth_cookies,
)
from app.core.auth.dependencies import get_current_user
from app.core.auth.jwt import (
    REFRESH_TOKEN_TYPE,
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.auth.password import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    hash_password,
    verify_password,
)
from app.core.auth.tokens import (
    detect_and_burn_replay,
    find_active_refresh_token,
    find_refresh_token_record,
    revoke_all_user_tokens,
    revoke_token,
    store_refresh_token,
)
from app.data.database import get_db
from app.data.dossier_models import DossierCheckpoint, DossierFact
from app.data.models import (
    ChatSession,
    User,
    UserConsent,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================================
# Вспомогательные
# ============================================================================


def _client_meta(request: Request) -> tuple[str, str]:
    """Извлечь IP и User-Agent клиента (для аудита refresh-токенов и consents)."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        ip = xff.split(",")[0].strip()
    elif request.client:
        ip = request.client.host
    else:
        ip = ""
    ua = request.headers.get("user-agent", "")
    return ip[:45], ua[:500]


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        subscription_tier=user.subscription_tier,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat(),
        deletion_scheduled_at=(
            user.deletion_scheduled_at.isoformat()
            if user.deletion_scheduled_at else None
        ),
    )


async def _issue_tokens_and_set_cookies(
    *,
    db: AsyncSession,
    user_id: str,
    response: Response,
    ip: str,
    ua: str,
) -> None:
    """Выпустить пару access+refresh, записать refresh в БД, поставить cookies."""
    access_token, _ = create_access_token(user_id)
    refresh_token, refresh_jti = create_refresh_token(user_id)

    await store_refresh_token(
        db,
        token=refresh_token,
        jti=refresh_jti,
        user_id=user_id,
        user_agent=ua,
        ip_address=ip,
    )

    set_auth_cookies(
        response,
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ============================================================================
# POST /register
# ============================================================================


@router.post("/register", response_model=AuthResponse)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Зарегистрировать нового пользователя.

    Шаги:
    1. Валидация пароля (длина).
    2. Проверка что email не занят.
    3. Создание User с Argon2-хешем пароля.
    4. Опциональная миграция guest_id → user_id (сессии, досье, согласия).
    5. Запись согласий (либо мигрированных, либо новых из payload).
    6. Выпуск токенов, установка cookies.
    """
    # Валидация длины пароля (Pydantic уже проверил min/max, но на всякий
    # случай явная проверка против констант password.py)
    if not (MIN_PASSWORD_LENGTH <= len(payload.password) <= MAX_PASSWORD_LENGTH):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} chars",
        )

    # Email уникален
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Создаём пользователя
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        is_verified=True,  # MVP: без email-верификации (см. ROADMAP)
    )
    db.add(user)
    await db.flush()  # чтобы получить user.id

    ip, ua = _client_meta(request)

    # Миграция guest → user (сессии, досье, согласия)
    if payload.guest_id:
        await _migrate_guest_to_user(
            db, guest_id=payload.guest_id, user_id=user.id,
        )

    # Проверка / запись согласий
    await _ensure_required_consents(
        db,
        user_id=user.id,
        guest_id=payload.guest_id,
        new_consents=payload.consents,
        ip=ip,
        ua=ua,
    )

    # Токены
    await _issue_tokens_and_set_cookies(
        db=db, user_id=user.id, response=response, ip=ip, ua=ua,
    )

    await db.commit()
    logger.info("Register: user=%s email=%s", user.id[:8], user.email)

    return AuthResponse(user=_to_user_response(user))


# ============================================================================
# POST /login
# ============================================================================


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Войти по email + паролю.

    На любую ошибку (нет юзера / неправильный пароль / отсутствие хеша)
    отвечаем одинаково — 401, чтобы не утекали детали.
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user: User | None = result.scalar_one_or_none()

    # Запускаем verify даже если user is None — чтобы время ответа было
    # одинаковым в обоих случаях (защита от user enumeration по таймингу).
    # Pwdlib делает constant-time сравнение.
    dummy_hash = "$argon2id$v=19$m=65536,t=3,p=4$" + ("A" * 22) + "$" + ("A" * 43)
    password_ok = verify_password(
        payload.password,
        user.password_hash if (user and user.password_hash) else dummy_hash,
    )

    if user is None or not user.password_hash or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    ip, ua = _client_meta(request)
    await _issue_tokens_and_set_cookies(
        db=db, user_id=user.id, response=response, ip=ip, ua=ua,
    )
    await db.commit()
    logger.info("Login: user=%s", user.id[:8])

    return AuthResponse(user=_to_user_response(user))


# ============================================================================
# POST /refresh
# ============================================================================


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    _: RefreshRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Обновить access-токен по refresh.

    Логика:
    1. Достать refresh из httpOnly cookie.
    2. Декодировать как refresh JWT.
    3. Найти запись в БД.
    4. Если запись revoked → это replay-атака, отзываем ВСЕ токены этого
       пользователя и возвращаем 401.
    5. Иначе — старый revoke (с replaced_by на новый), новый выпускаем,
       cookies обновляем.
    """
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )

    # Декодируем
    try:
        payload = decode_token(refresh_token, expected_type=REFRESH_TOKEN_TYPE)
    except TokenError as e:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {e}",
        )

    # Сначала ищем ЛЮБУЮ запись (включая revoked) — для детекции replay
    record = await find_refresh_token_record(db, token=refresh_token)
    if record is None:
        # Токен валидный по подписи, но в БД его нет (например, БД пересоздана).
        # Считаем это аномалией и отказываем.
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    if record.revoked_at is not None:
        # REPLAY-атака: пришёл уже-отозванный токен.
        # Burn всю цепочку этого пользователя.
        logger.warning(
            "Refresh replay detected for user=%s, burning all tokens",
            record.user_id[:8],
        )
        await detect_and_burn_replay(db, suspicious_token_record=record)
        await db.commit()
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token replay detected, all sessions revoked",
        )

    # SQLite не сохраняет таймзону — нормализуем naive → UTC
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Пользователь ещё существует?
    user = await db.get(User, payload.sub)
    if user is None:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Rotation: новый refresh, старый revoke
    ip, ua = _client_meta(request)
    new_access, _ = create_access_token(user.id)
    new_refresh, new_jti = create_refresh_token(user.id)

    await store_refresh_token(
        db,
        token=new_refresh,
        jti=new_jti,
        user_id=user.id,
        user_agent=ua,
        ip_address=ip,
    )
    await revoke_token(db, record=record, replaced_by=new_jti)
    await db.commit()

    set_auth_cookies(
        response,
        access_token=new_access,
        refresh_token=new_refresh,
    )

    return AuthResponse(user=_to_user_response(user))


# ============================================================================
# POST /logout
# ============================================================================


@router.post("/logout")
async def logout(
    payload: LogoutRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, bool]:
    """Выйти.

    - everywhere=False (default): отзываем только текущий refresh.
    - everywhere=True: отзываем все refresh-токены пользователя.

    Cookies очищаются в любом случае.
    """
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    if refresh_token:
        record = await find_refresh_token_record(db, token=refresh_token)
        if record is not None and record.revoked_at is None:
            if payload.everywhere:
                await revoke_all_user_tokens(db, user_id=record.user_id)
            else:
                await revoke_token(db, record=record)
            await db.commit()

    clear_auth_cookies(response)
    return {"ok": True}


# ============================================================================
# GET /me
# ============================================================================


@router.get("/me", response_model=UserResponse)
async def me(
    user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Получить данные текущего пользователя."""
    return _to_user_response(user)


# ============================================================================
# DELETE /me — запросить удаление аккаунта (soft-delete с 7-day grace period)
# ============================================================================


@router.delete("/me")
async def delete_account(
    user: Annotated[User, Depends(get_current_user)],
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Запланировать удаление аккаунта через 7 дней.

    Что происходит сразу:
    - User.deletion_scheduled_at = now() + 7 days
    - Все refresh-токены пользователя отзываются (вылет со всех устройств)
    - Cookies очищаются

    Что НЕ происходит сразу:
    - Сообщения и сессии не трогаются (они станут осиротевшими только через 7 дней)
    - Досье не трогается (тоже через 7 дней)
    - Подписки не отменяются здесь (это в Блоке F через ЮKassa)

    В течение 7 дней пользователь может залогиниться обратно и
    вызвать `POST /me/cancel-deletion`, чтобы отменить.

    Если не отменит — Celery-таск ежедневно вызывает
    `finalize_pending_deletions()`, который реально:
    - Отвязывает сессии и сообщения (для data flywheel — текст уже
      обезличен через ReflectionAgent)
    - Удаляет досье целиком
    - Удаляет согласия
    - Удаляет refresh-токены и пользователя
    """
    scheduled = await schedule_account_deletion(db, user=user)
    await db.commit()

    clear_auth_cookies(response)
    return {
        "ok": True,
        "scheduled_at": scheduled.isoformat(),
        "grace_days": 7,
        "message": (
            "Аккаунт будет удалён через 7 дней. До этого момента ты можешь "
            "войти снова и отменить удаление. Подписки автоматически "
            "не отменяются — отмени их отдельно, если они есть."
        ),
    }


# ============================================================================
# POST /me/cancel-deletion — отменить запланированное удаление
# ============================================================================


@router.post("/me/cancel-deletion")
async def cancel_deletion(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Отменить запланированное удаление аккаунта.

    Идемпотентно: если удаление не было запланировано — тихий ok.
    """
    if user.deletion_scheduled_at is None:
        return {"ok": True, "was_scheduled": False}

    await cancel_account_deletion(db, user=user)
    await db.commit()
    return {"ok": True, "was_scheduled": True}


# ============================================================================
# Внутренние хелперы — миграция гостя → пользователя
# ============================================================================


async def _migrate_guest_to_user(
    db: AsyncSession, *, guest_id: str, user_id: str,
) -> None:
    """Привязать гостевые ChatSession к user_id.

    Также мигрирует досье (DossierFact, DossierCheckpoint) — их идентификатор
    был guest_id (так делали на этапе чисто-гостевой работы).

    Идемпотентно: если ничего не найдено, ничего не делает.
    """
    # ChatSession: WHERE guest_id = ? AND user_id IS NULL
    sessions = await db.execute(
        select(ChatSession).where(
            (ChatSession.guest_id == guest_id) & (ChatSession.user_id.is_(None)),
        ),
    )
    migrated_sessions = 0
    for session in sessions.scalars().all():
        session.user_id = user_id
        migrated_sessions += 1

    # DossierFact: user_id у факта мог быть guest_id'ом.
    # Это особенность нашей текущей схемы: на гостевом MVP мы кладём
    # guest_id в DossierFact.user_id, а потом мигрируем.
    facts = await db.execute(
        select(DossierFact).where(DossierFact.user_id == guest_id),
    )
    migrated_facts = 0
    for fact in facts.scalars().all():
        fact.user_id = user_id
        migrated_facts += 1

    # DossierCheckpoint аналогично
    checkpoints = await db.execute(
        select(DossierCheckpoint).where(
            DossierCheckpoint.user_id == guest_id,
        ),
    )
    for cp in checkpoints.scalars().all():
        cp.user_id = user_id

    if migrated_sessions or migrated_facts:
        logger.info(
            "Guest→User migration: sessions=%d facts=%d (guest=%s, user=%s)",
            migrated_sessions, migrated_facts, guest_id[:8], user_id[:8],
        )


async def _ensure_required_consents(
    db: AsyncSession,
    *,
    user_id: str,
    guest_id: str | None,
    new_consents: list,
    ip: str,
    ua: str,
) -> None:
    """Убедиться, что у пользователя есть все 3 обязательных согласия.

    Логика:
    1. Если guest_id указан — мигрируем существующие согласия (привязываем к user_id).
    2. Если после миграции каких-то типов не хватает — добавляем из new_consents.
    3. Если всё ещё не хватает — 400.

    Это правильно юридически: пользователь либо уже дал согласие как гость
    (через FirstVisitModal), либо даёт сейчас в форме регистрации.
    """
    # 1. Миграция consent guest_id → user_id
    # Собираем существующие типы прямо при миграции — не делаем повторный SELECT
    # после, чтобы не зависеть от порядка flush в SQLAlchemy.
    existing_types: set[str] = set()
    if guest_id:
        existing = await db.execute(
            select(UserConsent).where(
                (UserConsent.guest_id == guest_id)
                & (UserConsent.revoked_at.is_(None)),
            ),
        )
        for consent in existing.scalars().all():
            consent.user_id = user_id
            existing_types.add(consent.consent_type)

    # На случай если у user_id уже были consents (например, повторная регистрация
    # с тем же email после удаления — это исключено логикой выше, но защитимся)
    if not guest_id or not existing_types:
        already_user = await db.execute(
            select(UserConsent).where(
                (UserConsent.user_id == user_id)
                & (UserConsent.revoked_at.is_(None)),
            ),
        )
        existing_types.update(c.consent_type for c in already_user.scalars().all())

    # 3. Дополняем из new_consents
    for item in new_consents:
        if item.consent_type in existing_types:
            continue  # уже есть, skip
        consent = UserConsent(
            user_id=user_id,
            consent_type=item.consent_type,
            document_version=item.document_version,
            ip_address=ip,
            user_agent=ua,
        )
        db.add(consent)
        existing_types.add(item.consent_type)

    # 4. Проверка что всё необходимое есть
    missing = REQUIRED_CONSENTS - existing_types
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Missing required consents: {sorted(missing)}. "
                "Either pass them in `consents` field or accept them "
                "as a guest first via /api/consent."
            ),
        )
