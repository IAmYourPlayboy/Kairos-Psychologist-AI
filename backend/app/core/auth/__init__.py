"""Аутентификация: JWT + Argon2 + httpOnly cookies (Блок C1, Сессия 22).

Архитектура:
- `password.py` — хеширование паролей через Argon2id (PHC winner).
- `jwt.py` — выпуск и валидация access + refresh JWT.
- `tokens.py` — работа с refresh-токенами в БД (rotation, revocation).
- `dependencies.py` — FastAPI dependencies `get_current_user`, `get_optional_user`.
- `cookies.py` — установка/снятие httpOnly cookies для JWT.

Стратегия:
- access_token: 15 мин, в httpOnly cookie, проверяется без БД (быстро).
- refresh_token: 30 дней, в httpOnly cookie + хеш в БД, отзываемый.
- Refresh rotation: при использовании refresh выпускается новый, старый
  помечается revoked. Использование уже-revoked токена → отзыв всей цепочки
  (OWASP-pattern против replay-атак).

Безопасность:
- httpOnly: защита от XSS (JS не имеет доступа к cookie)
- Secure: только HTTPS (отключаем в dev через env)
- SameSite=Lax: защита от CSRF (для большинства запросов)
- В БД хранится SHA-256 хеш refresh-токена, не сам токен
"""

from app.core.auth.dependencies import (
    get_current_user,
    get_optional_user,
)
from app.core.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.auth.password import hash_password, verify_password

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_user",
    "get_optional_user",
    "hash_password",
    "verify_password",
]
