"""Тесты sessions API (Блок C3, Сессия 22).

Покрытие:
- list: только свои сессии возвращаются, сортировка
- get: 404 на чужую, 200 со своей с messages
- delete: каскад
- migrate: гостевые сессии и факты переезжают
- isolation: пользователь A не видит сессии пользователя B
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_sessions_api.db"
os.environ["LLM_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-32-chars-min-aaa"

from app.data.database import (
    async_session_factory,
    create_all_tables,
    drop_all_tables,
)
from app.data.dossier_models import DossierFact
from app.data.models import ChatSession, Message, User


def _full_consents() -> list[dict]:
    return [
        {"consent_type": "terms_of_service"},
        {"consent_type": "data_processing"},
        {"consent_type": "research_anonymized"},
    ]


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    await drop_all_tables()
    await create_all_tables()
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await drop_all_tables()


async def _register(
    client: AsyncClient, *, email: str, password: str = "secret-password",
    guest_id: str | None = None,
) -> dict:
    payload: dict = {
        "email": email, "password": password, "consents": _full_consents(),
    }
    if guest_id:
        payload["guest_id"] = guest_id
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


async def _add_session_with_messages(
    user_id: str | None,
    guest_id: str | None = None,
    *,
    n_messages: int = 2,
    crisis_level_max: str = "normal",
) -> str:
    """Хелпер: добавляет ChatSession с сообщениями. Возвращает session_id."""
    session_id = str(uuid4())
    base_time = datetime.now(timezone.utc)

    async with async_session_factory() as db:
        session = ChatSession(
            id=session_id,
            user_id=user_id,
            guest_id=guest_id,
            crisis_level_max=crisis_level_max,
            message_count=n_messages,
        )
        db.add(session)
        await db.flush()

        for i in range(n_messages):
            db.add(Message(
                id=str(uuid4()),
                session_id=session_id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"сообщение #{i}",
                server_timestamp=base_time + timedelta(seconds=i),
            ))
        await db.commit()
    return session_id


# ============================================================================
# LIST
# ============================================================================


class TestListSessions:
    async def test_unauthenticated_401(self, client: AsyncClient) -> None:
        response = await client.get("/api/sessions")
        assert response.status_code == 401

    async def test_empty_for_new_user(self, client: AsyncClient) -> None:
        await _register(client, email="empty@example.com")
        response = await client.get("/api/sessions")
        assert response.status_code == 200
        assert response.json()["sessions"] == []

    async def test_returns_own_sessions(self, client: AsyncClient) -> None:
        data = await _register(client, email="own@example.com")
        user_id = data["user"]["id"]

        await _add_session_with_messages(user_id=user_id, n_messages=2)
        await _add_session_with_messages(user_id=user_id, n_messages=4)

        response = await client.get("/api/sessions")
        assert response.status_code == 200
        sessions = response.json()["sessions"]
        assert len(sessions) == 2

    async def test_does_not_return_other_users_sessions(
        self, client: AsyncClient,
    ) -> None:
        # User A
        data_a = await _register(client, email="a@example.com")
        user_a = data_a["user"]["id"]
        await _add_session_with_messages(user_id=user_a)

        # User B
        await client.post("/api/auth/logout", json={})
        client.cookies.clear()
        data_b = await _register(client, email="b@example.com")
        user_b = data_b["user"]["id"]
        await _add_session_with_messages(user_id=user_b)
        await _add_session_with_messages(user_id=user_b)

        # User B видит только 2 свои сессии, не 3
        response = await client.get("/api/sessions")
        sessions = response.json()["sessions"]
        assert len(sessions) == 2

    async def test_session_has_title_from_first_user_message(
        self, client: AsyncClient,
    ) -> None:
        data = await _register(client, email="title@example.com")
        user_id = data["user"]["id"]
        await _add_session_with_messages(user_id=user_id, n_messages=2)

        response = await client.get("/api/sessions")
        sessions = response.json()["sessions"]
        # Первое user-сообщение в _add_session_with_messages — "сообщение #0"
        assert sessions[0]["title"].startswith("сообщение")


# ============================================================================
# GET ONE
# ============================================================================


class TestGetSession:
    async def test_404_for_other_user_session(self, client: AsyncClient) -> None:
        # User A создаёт сессию
        data_a = await _register(client, email="ga@example.com")
        sid = await _add_session_with_messages(user_id=data_a["user"]["id"])

        # Logout A, login B
        await client.post("/api/auth/logout", json={})
        client.cookies.clear()
        await _register(client, email="gb@example.com")

        # B пытается прочитать сессию A — 404
        response = await client.get(f"/api/sessions/{sid}")
        assert response.status_code == 404

    async def test_returns_messages(self, client: AsyncClient) -> None:
        data = await _register(client, email="msgs@example.com")
        sid = await _add_session_with_messages(
            user_id=data["user"]["id"], n_messages=3,
        )
        response = await client.get(f"/api/sessions/{sid}")
        assert response.status_code == 200
        body = response.json()
        assert body["session"]["id"] == sid
        assert len(body["messages"]) == 3
        # Сообщения отсортированы по времени
        assert body["messages"][0]["role"] == "user"
        assert body["messages"][1]["role"] == "assistant"

    async def test_unknown_session_404(self, client: AsyncClient) -> None:
        await _register(client, email="ghost@example.com")
        response = await client.get(f"/api/sessions/{uuid4()}")
        assert response.status_code == 404


# ============================================================================
# DELETE
# ============================================================================


class TestDeleteSession:
    async def test_success(self, client: AsyncClient) -> None:
        data = await _register(client, email="del@example.com")
        sid = await _add_session_with_messages(user_id=data["user"]["id"])

        response = await client.delete(f"/api/sessions/{sid}")
        assert response.status_code == 200

        # Проверяем что сессия и сообщения удалены
        from sqlalchemy import select
        async with async_session_factory() as db:
            assert await db.get(ChatSession, sid) is None
            msgs = await db.execute(
                select(Message).where(Message.session_id == sid),
            )
            assert msgs.scalar_one_or_none() is None

    async def test_other_user_404(self, client: AsyncClient) -> None:
        data_a = await _register(client, email="da@example.com")
        sid = await _add_session_with_messages(user_id=data_a["user"]["id"])

        await client.post("/api/auth/logout", json={})
        client.cookies.clear()
        await _register(client, email="db@example.com")

        response = await client.delete(f"/api/sessions/{sid}")
        assert response.status_code == 404


# ============================================================================
# MIGRATE
# ============================================================================


class TestMigrate:
    async def test_migrates_guest_sessions(self, client: AsyncClient) -> None:
        guest_id = str(uuid4())
        # Гостевая сессия (user_id=NULL, guest_id=...)
        await _add_session_with_messages(user_id=None, guest_id=guest_id)

        # Регистрация БЕЗ guest_id — миграция не сработала автоматически
        await _register(client, email="m@example.com")

        # Ручная миграция через эндпоинт
        response = await client.post(
            "/api/sessions/migrate",
            json={"guest_id": guest_id},
        )
        assert response.status_code == 200
        assert response.json()["sessions_migrated"] == 1

        # Проверяем что в /api/sessions она появилась
        sessions = await client.get("/api/sessions")
        assert len(sessions.json()["sessions"]) == 1

    async def test_migrates_dossier_facts(self, client: AsyncClient) -> None:
        guest_id = str(uuid4())

        # Гостевой факт (user_id = guest_id, по нашей схеме)
        async with async_session_factory() as db:
            db.add(DossierFact(
                id=str(uuid4()),
                user_id=guest_id,
                folder="family",
                subfolder="parents",
                summary="Папа пьёт",
                tags=[],
                severity=0.7,
                confidence=0.9,
            ))
            await db.commit()

        # Регистрация и миграция
        await _register(client, email="dm@example.com")
        response = await client.post(
            "/api/sessions/migrate",
            json={"guest_id": guest_id},
        )
        assert response.status_code == 200
        assert response.json()["facts_migrated"] == 1

    async def test_idempotent(self, client: AsyncClient) -> None:
        guest_id = str(uuid4())
        await _register(client, email="idem@example.com")

        # Первый раз — мигрировать нечего
        r1 = await client.post(
            "/api/sessions/migrate", json={"guest_id": guest_id},
        )
        assert r1.status_code == 200
        # Второй раз — тоже
        r2 = await client.post(
            "/api/sessions/migrate", json={"guest_id": guest_id},
        )
        assert r2.status_code == 200

    async def test_unauthenticated_401(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/sessions/migrate", json={"guest_id": str(uuid4())},
        )
        assert response.status_code == 401
