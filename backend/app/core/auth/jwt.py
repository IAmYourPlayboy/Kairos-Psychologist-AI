"""JWT: выпуск и валидация access/refresh токенов.

Структура токена (payload):
    sub:  user_id (UUID-строка)
    type: "access" | "refresh"
    exp:  unix-timestamp истечения
    iat:  unix-timestamp выпуска
    jti:  UUID этого токена (для refresh — индекс в БД для отзыва)

Зачем разделять access и refresh:
- access: 15 мин, проверяется без БД (быстро, на каждом запросе)
- refresh: 30 дней, в БД (отзываемый при logout/смене пароля)

`type` поле защищает от путаницы: refresh токен нельзя использовать как
access (validate_access_token проверяет type), и наоборот.

`jti` (JWT ID) — уникальный идентификатор токена. Нужен только для refresh
(чтобы записать его в БД и отзывать). У access токена тоже есть, но мы его
не используем (access не отзываемый).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt as pyjwt

from app.config import settings


# Типы токенов
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


# ============================================================================
# Структура декодированного токена
# ============================================================================


@dataclass(frozen=True)
class TokenPayload:
    """Расшифрованная нагрузка JWT.

    Frozen — иммутабельный, чтобы случайно не модифицировать после декода.
    """

    sub: str           # user_id
    type: str          # "access" | "refresh"
    exp: int           # unix-timestamp истечения
    iat: int           # unix-timestamp выпуска
    jti: str           # уникальный ID токена

    @property
    def is_access(self) -> bool:
        return self.type == ACCESS_TOKEN_TYPE

    @property
    def is_refresh(self) -> bool:
        return self.type == REFRESH_TOKEN_TYPE


# ============================================================================
# Исключения
# ============================================================================


class TokenError(Exception):
    """Базовый класс ошибок работы с токенами."""


class TokenExpiredError(TokenError):
    """Токен истёк по `exp`."""


class TokenInvalidError(TokenError):
    """Токен повреждён, подпись неверна, или payload некорректен."""


class TokenWrongTypeError(TokenError):
    """Токен валидный, но не того типа (access вместо refresh или наоборот)."""


# ============================================================================
# Создание токенов
# ============================================================================


def create_access_token(user_id: str) -> tuple[str, str]:
    """Создать access JWT.

    Returns:
        (encoded_jwt, jti) — токен и его уникальный ID.
        jti обычно не используется для access (нет БД), но возвращаем
        для симметрии API и для логов.
    """
    return _create_token(
        user_id=user_id,
        token_type=ACCESS_TOKEN_TYPE,
        expires_delta=timedelta(
            minutes=settings.jwt_access_token_expire_minutes,
        ),
    )


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """Создать refresh JWT.

    Returns:
        (encoded_jwt, jti) — токен и его уникальный ID.
        jti используется для записи токена в `refresh_tokens` таблицу.
    """
    return _create_token(
        user_id=user_id,
        token_type=REFRESH_TOKEN_TYPE,
        expires_delta=timedelta(
            days=settings.jwt_refresh_token_expire_days,
        ),
    )


def _create_token(
    *,
    user_id: str,
    token_type: str,
    expires_delta: timedelta,
) -> tuple[str, str]:
    """Внутренний хелпер: общая логика выпуска токенов."""
    now = datetime.now(timezone.utc)
    expires_at = now + expires_delta
    jti = str(uuid4())

    payload = {
        "sub": user_id,
        "type": token_type,
        "exp": int(expires_at.timestamp()),
        "iat": int(now.timestamp()),
        "jti": jti,
    }

    token = pyjwt.encode(
        payload,
        settings.effective_jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return token, jti


# ============================================================================
# Декодирование токенов
# ============================================================================


def decode_token(token: str, *, expected_type: str | None = None) -> TokenPayload:
    """Декодировать и проверить токен.

    Args:
        token: JWT-строка.
        expected_type: если задан, проверяет совпадение `type` в payload.
            Используется для защиты от смешения access и refresh.

    Returns:
        TokenPayload — расшифрованная нагрузка.

    Raises:
        TokenExpiredError: если `exp` в прошлом.
        TokenInvalidError: если подпись неверна или payload поломан.
        TokenWrongTypeError: если expected_type не совпадает.
    """
    try:
        decoded = pyjwt.decode(
            token,
            settings.effective_jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except pyjwt.ExpiredSignatureError as e:
        raise TokenExpiredError(str(e)) from e
    except pyjwt.InvalidTokenError as e:
        # InvalidSignatureError, DecodeError, InvalidIssuerError и др.
        raise TokenInvalidError(str(e)) from e

    # Все обязательные поля должны быть на месте
    try:
        payload = TokenPayload(
            sub=str(decoded["sub"]),
            type=str(decoded["type"]),
            exp=int(decoded["exp"]),
            iat=int(decoded["iat"]),
            jti=str(decoded["jti"]),
        )
    except (KeyError, ValueError, TypeError) as e:
        raise TokenInvalidError(f"malformed payload: {e}") from e

    if expected_type is not None and payload.type != expected_type:
        raise TokenWrongTypeError(
            f"expected token type '{expected_type}', got '{payload.type}'",
        )

    return payload
