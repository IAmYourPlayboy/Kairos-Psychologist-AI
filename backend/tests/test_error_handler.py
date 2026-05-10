"""Тесты глобального обработчика HTTP-исключений.

Проверяем контракт: ``error.message`` в ответе — ВСЕГДА строка,
даже если endpoint передал ``detail=dict`` (нужно отдать ``code`` +
доп. поля).

Контекст: до Сессии 27 ``_http_exception_handler`` клал ``exc.detail``
в ``message`` как есть. Если это был dict, JSONResponse сериализовал его
как объект, и фронтенд видел ``"[object Object]"`` (JS toString при
интерполяции объекта в строку).

Пример: ``chat.py`` при ``account_pending_deletion`` отдаёт
``detail={"code": ..., "message": ..., "scheduled_at": ...}``.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient

os.environ.setdefault(
    "DATABASE_URL", "sqlite+aiosqlite:///./kairos_test_error_handler.db",
)
os.environ.setdefault("LLM_API_KEY", "test-key")

from app.middleware.error_handler import register_error_handlers


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Мини-приложение с зарегистрированными обработчиками и парой тестовых эндпоинтов."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/raise-string-detail")
    async def _raise_str() -> None:
        raise HTTPException(status_code=400, detail="простая строка")

    @app.get("/raise-dict-detail")
    async def _raise_dict() -> None:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "account_pending_deletion",
                "message": "Твой аккаунт помечен на удаление.",
                "scheduled_at": "2026-05-17T13:04:52",
            },
        )

    @app.get("/raise-dict-without-message")
    async def _raise_dict_no_msg() -> None:
        raise HTTPException(
            status_code=400,
            detail={"code": "some_code", "extra": 123},
        )

    @app.get("/raise-dict-empty")
    async def _raise_dict_empty() -> None:
        raise HTTPException(status_code=400, detail={})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Обратная совместимость: detail=str
# ============================================================================


@pytest.mark.asyncio
async def test_string_detail_goes_into_message(client: AsyncClient) -> None:
    """Контракт не ломается для старых эндпоинтов с detail=str."""
    response = await client.get("/raise-string-detail")
    assert response.status_code == 400

    body = response.json()
    assert body["error"]["message"] == "простая строка"
    assert body["error"]["details"] is None
    assert body["error"]["status"] == 400
    assert body["error"]["type"] == "http_exception"


# ============================================================================
# Новое: detail=dict → message как строка, details = весь dict
# ============================================================================


@pytest.mark.asyncio
async def test_dict_detail_extracts_message_string(client: AsyncClient) -> None:
    """Главный тест: dict в detail → message = строка из ключа 'message'.

    Это защита от бага "[object Object]" — frontend ApiClientError
    получает `message` и передаёт в Error(), если там объект, JS делает
    toString() → "[object Object]".
    """
    response = await client.get("/raise-dict-detail")
    assert response.status_code == 403

    body = response.json()
    # message — ровно та строка, что была в detail['message']
    assert body["error"]["message"] == "Твой аккаунт помечен на удаление."
    assert isinstance(body["error"]["message"], str), (
        "message ДОЛЖНО быть строкой (frontend-контракт)"
    )

    # Весь dict сохраняется в details — frontend может прочитать code,
    # scheduled_at и т.д. для специальной обработки
    details = body["error"]["details"]
    assert details == {
        "code": "account_pending_deletion",
        "message": "Твой аккаунт помечен на удаление.",
        "scheduled_at": "2026-05-17T13:04:52",
    }


@pytest.mark.asyncio
async def test_dict_without_message_falls_back_to_code(client: AsyncClient) -> None:
    """Если в dict нет 'message' — берём 'code' как fallback.

    Чтобы даже не совсем правильные endpoint'ы не выдавали мусор клиенту.
    """
    response = await client.get("/raise-dict-without-message")
    assert response.status_code == 400

    body = response.json()
    assert body["error"]["message"] == "some_code"
    assert isinstance(body["error"]["message"], str)
    assert body["error"]["details"] == {"code": "some_code", "extra": 123}


@pytest.mark.asyncio
async def test_empty_dict_detail_produces_default_message(client: AsyncClient) -> None:
    """Пустой dict — последний fallback на 'error'. UI увидит что-то, не '{}'."""
    response = await client.get("/raise-dict-empty")
    assert response.status_code == 400

    body = response.json()
    assert isinstance(body["error"]["message"], str)
    # ok если это "error" или любая короткая строка — главное что не пустой dict
    assert body["error"]["message"].strip() != ""
    assert body["error"]["message"] != "{}"


# ============================================================================
# Регрессия для chat.py pending-deletion
# ============================================================================


@pytest.mark.asyncio
async def test_pending_deletion_shape_matches_frontend_contract(client: AsyncClient) -> None:
    """Имитирует ровно тот detail, что отдаёт chat.py при account_pending_deletion.

    Перед Сессией 27: фронтенд получал ``{error: {message: {code:..., message:...}}}``
    и выводил ``[object Object]``. После фикса: ``{error: {message: str, details: {...}}}``,
    и frontend видит человеческий текст.
    """
    response = await client.get("/raise-dict-detail")
    body = response.json()

    # То что получит фронтенд (lib/api.ts::ApiClientError)
    error_payload = body["error"]

    # После фикса: message всегда строка
    assert isinstance(error_payload["message"], str)
    assert "аккаунт" in error_payload["message"].lower()

    # details содержит структурированные данные для frontend-логики
    # (например, frontend может показать countdown на scheduled_at)
    assert error_payload["details"]["code"] == "account_pending_deletion"
    assert "scheduled_at" in error_payload["details"]
