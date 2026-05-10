"""Глобальная обработка ошибок FastAPI.

Цели:
- Никогда не отдавать stacktrace клиенту (только в логи)
- Стандартный JSON-формат для всех ошибок
- Сохранять X-Request-ID для трейсинга

Регистрация (в main.py):

    from app.middleware.error_handler import register_error_handlers
    register_error_handlers(app)
"""

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str | None:
    """Извлечь X-Request-ID из заголовков запроса (если RequestIDMiddleware его установил)."""
    return request.headers.get("X-Request-ID")


async def _http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Обработчик HTTP-исключений (raise HTTPException(...)).

    Контракт фронтенда (lib/api.ts::ApiClientError): ``error.message``
    ВСЕГДА строка. Если эндпоинт передал ``detail=dict`` (нужно отдать
    доп. поля: ``code``, ``scheduled_at``, etc.) — извлекаем ``message``
    как строку, а весь dict кладём в ``details``.

    Пример: ``chat.py`` при ``account_pending_deletion`` передаёт
    ``detail={"code": ..., "message": ..., "scheduled_at": ...}``.
    Без нормализации JSONResponse сериализовал бы dict в ``message``,
    и фронтенд получал бы ``"[object Object]"`` (JS toString при
    интерполяции объекта в строку).
    """
    detail = exc.detail
    if isinstance(detail, dict):
        # Стандартный формат: {"code": ..., "message": str, ...}
        message = str(detail.get("message") or detail.get("code") or "error")
        details: object | None = detail
    else:
        message = str(detail)
        details = None

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_exception",
                "status": exc.status_code,
                "message": message,
                "details": details,
                "request_id": _request_id(request),
            }
        },
    )


async def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Обработчик ошибок валидации Pydantic (422)."""
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "status": 422,
                "message": "Ошибка валидации запроса",
                "details": exc.errors(),
                "request_id": _request_id(request),
            }
        },
    )


async def _unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Обработчик всего, что не было обработано выше.

    КЛИЕНТУ:  только общий код 500 без деталей.
    В ЛОГИ:   полный stacktrace для отладки.
    """
    request_id = _request_id(request)
    logger.error(
        "Unhandled exception (request_id=%s, path=%s):\n%s",
        request_id,
        request.url.path,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "status": 500,
                "message": "Внутренняя ошибка сервера. Попробуй позже.",
                "request_id": request_id,
            }
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    """Подключить все обработчики ошибок к приложению."""
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
