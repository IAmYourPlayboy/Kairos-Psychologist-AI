"""Тесты API досье (GET / DELETE).

ФЗ-152: пользователь должен иметь возможность посмотреть и удалить
всё что Кайрос о нём знает.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Отдельный файл SQLite для этих тестов — НЕ трогаем dev-БД.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_dossier_api.db"
os.environ["LLM_API_KEY"] = "test-key"

from app.core.perception.dossier import DossierService
from app.data.database import (
    async_session_factory,
    create_all_tables,
    drop_all_tables,
)
from app.data.models import User


@pytest_asyncio.fixture
async def client_with_user() -> AsyncIterator[tuple[AsyncClient, str]]:
    """Создаёт чистую БД с одним пользователем и одним фактом."""
    await drop_all_tables()
    await create_all_tables()
    user_id = str(uuid4())

    async with async_session_factory() as db:
        db.add(User(id=user_id, email="t@e.com"))
        await db.commit()

    async with async_session_factory() as db:
        service = DossierService(db)
        await service.add_fact(
            user_id=user_id,
            folder="family",
            subfolder="parents",
            summary="Папа пьёт",
            tags=["dad-alcohol"],
            severity=0.8,
            confidence=0.9,
            quotes=[],
        )

    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, user_id

    await drop_all_tables()


# ============================================================================
# GET /api/dossier
# ============================================================================


async def test_list_dossier_returns_facts(client_with_user):
    client, user_id = client_with_user
    resp = await client.get(f"/api/dossier?user_id={user_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["facts"]) == 1
    assert data["facts"][0]["summary"] == "Папа пьёт"
    assert data["facts"][0]["folder"] == "family"
    assert data["facts"][0]["subfolder"] == "parents"


async def test_list_returns_empty_for_unknown_user(client_with_user):
    """Неизвестный user_id → 200 с пустым списком (а не 404).

    Это намеренно: чтобы UI мог отрисовать «Кайрос ещё ничего не знает»
    вместо ошибки.
    """
    client, _ = client_with_user
    other_user = str(uuid4())
    resp = await client.get(f"/api/dossier?user_id={other_user}")
    assert resp.status_code == 200
    assert resp.json()["facts"] == []


# ============================================================================
# DELETE /api/dossier/{fact_id}
# ============================================================================


async def test_delete_one_fact(client_with_user):
    client, user_id = client_with_user
    list_resp = await client.get(f"/api/dossier?user_id={user_id}")
    fact_id = list_resp.json()["facts"][0]["id"]

    del_resp = await client.delete(
        f"/api/dossier/{fact_id}?user_id={user_id}",
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["ok"] is True
    assert del_resp.json()["deleted_count"] == 1

    list_resp_after = await client.get(f"/api/dossier?user_id={user_id}")
    assert len(list_resp_after.json()["facts"]) == 0


async def test_delete_other_user_fact_forbidden(client_with_user):
    """Нельзя удалить факт другого пользователя."""
    client, user_id = client_with_user
    list_resp = await client.get(f"/api/dossier?user_id={user_id}")
    fact_id = list_resp.json()["facts"][0]["id"]

    other_user = str(uuid4())
    del_resp = await client.delete(
        f"/api/dossier/{fact_id}?user_id={other_user}",
    )
    assert del_resp.status_code in (403, 404)


# ============================================================================
# DELETE /api/dossier (всё досье)
# ============================================================================


async def test_delete_all_dossier(client_with_user):
    client, user_id = client_with_user
    del_resp = await client.delete(f"/api/dossier?user_id={user_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_count"] >= 1

    list_resp = await client.get(f"/api/dossier?user_id={user_id}")
    assert list_resp.json()["facts"] == []
