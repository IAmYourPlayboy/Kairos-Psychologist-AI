"""FastAPI dependencies для авторизации.

Два уровня защиты:

- `get_current_user` — обязательный. Если нет валидного токена → 401.
  Используется на эндпоинтах только для залогиненных (профиль, удаление аккаунта).

- `get_optional_user` — опциональный. Если токена нет/невалид → None.
  Используется на эндпоинтах, которые работают и для гостей (`/api/chat`).

Источник токена — httpOnly cookie `kairos_access`. Тело и заголовки
проверяем как fallback: это удобно для тестов через httpx.AsyncClient,
где cookies отправлять не всегда тривиально.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.cookies import ACCESS_COOKIE_NAME
from app.core.auth.jwt import (
    ACCESS_TOKEN_TYPE,
    TokenError,
    decode_token,
)
from app.data.database import get_db
from app.data.models import User


def _extract_access_token(request: Request) -> str | None:
    """Достать access-токен из запроса.

    Приоритет:
    1. Cookie `kairos_access` (основной канал в проде)
    2. Authorization: Bearer <token> (fallback для тестов и API-клиентов)
    """
    cookie = request.cookies.get(ACCESS_COOKIE_NAME)
    if cookie:
        return cookie

    auth_header = request.headers.get("authorization") or ""
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    return None


async def get_optional_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """Получить текущего пользователя, если залогинен.

    Возвращает None если:
    - токена нет
    - токен невалидный или истёк
    - пользователь удалён из БД (но токен ещё активен)

    НЕ выбрасывает исключения. Для эндпоинтов, работающих и с гостями.
    """
    token = _extract_access_token(request)
    if not token:
        return None

    try:
        payload = decode_token(token, expected_type=ACCESS_TOKEN_TYPE)
    except TokenError:
        return None

    user = await db.get(User, payload.sub)
    return user


async def get_current_user(
    user: Annotated[User | None, Depends(get_optional_user)],
) -> User:
    """Получить текущего пользователя или 401.

    Используется на защищённых эндпоинтах (профиль, удаление и т.д.).

    Это обёртка над `get_optional_user` — переиспользует ту же логику
    разбора токена, не дублируя код. FastAPI кеширует Depends в рамках
    одного запроса, так что нет лишних вызовов.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
