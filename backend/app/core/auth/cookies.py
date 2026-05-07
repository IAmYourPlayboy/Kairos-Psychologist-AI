"""Установка / снятие httpOnly cookies для JWT.

Зачем cookies, а не Authorization header:
- Защита от XSS: HttpOnly cookie недоступен JavaScript-у. Даже если
  атакующий внедрит JS, токен он не украдёт.
- Автоматическая отправка браузером: фронтенд не должен помнить токен.
- Это рекомендация OWASP для веб-приложений с сессией.

SameSite=Lax: защита от CSRF. Браузер не отправит cookie на cross-site
POST-запросы (когда зловредный сайт пытается выдать запрос от имени
пользователя). Lax — компромисс: для обычной навигации (GET по ссылке)
cookie отправляется, для form submit с другого домена — нет.

Secure=True (в проде): cookie отправляется только по HTTPS. В dev
оставляем False, чтобы работало через http://localhost.
"""

from __future__ import annotations

from datetime import timedelta

from fastapi import Response

from app.config import settings


# Имена cookies — единое место правды
ACCESS_COOKIE_NAME = "kairos_access"
REFRESH_COOKIE_NAME = "kairos_refresh"


def set_auth_cookies(
    response: Response, *, access_token: str, refresh_token: str,
) -> None:
    """Установить оба cookie в ответ.

    Используется при login, register и refresh.
    """
    # Access cookie — короткая жизнь (15 мин)
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        max_age=int(timedelta(
            minutes=settings.jwt_access_token_expire_minutes,
        ).total_seconds()),
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,  # type: ignore[arg-type]
        domain=settings.cookie_domain,
        path="/",
    )
    # Refresh cookie — длинная жизнь (30 дней).
    # Path ограничен на /api/auth/refresh: refresh-токен нужен только там,
    # на других эндпоинтах он не отправляется → меньше attack surface.
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=int(timedelta(
            days=settings.jwt_refresh_token_expire_days,
        ).total_seconds()),
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,  # type: ignore[arg-type]
        domain=settings.cookie_domain,
        path="/api/auth",
    )


def clear_auth_cookies(response: Response) -> None:
    """Удалить оба cookie из браузера.

    Используется при logout. Обнуляет cookie, ставя пустое значение
    с max_age=0. Браузер удалит его.
    """
    response.delete_cookie(
        key=ACCESS_COOKIE_NAME,
        domain=settings.cookie_domain,
        path="/",
    )
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        domain=settings.cookie_domain,
        path="/api/auth",
    )
