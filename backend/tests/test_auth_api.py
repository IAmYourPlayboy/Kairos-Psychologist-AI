"""Тесты auth API (Блок C1, Сессия 22).

Покрытие:
- register: успех / дубликат / без consents / с guest миграцией
- login: успех / неправильный пароль / несуществующий email
- me: залогинен / гость
- logout: один / everywhere
- refresh: успех с rotation / истёкший / replay detection / revoked
- delete account: успех / каскад / анонимизация consents

LLM не задействована — на этих эндпоинтах её нет, моки не нужны.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_auth_api.db"
os.environ["LLM_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-32-chars-min-aaa"

from app.data.database import (
    async_session_factory,
    create_all_tables,
    drop_all_tables,
)


# ============================================================================
# Фикстуры
# ============================================================================


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Чистая БД на каждый тест."""
    await drop_all_tables()
    await create_all_tables()
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await drop_all_tables()


def _full_consents() -> list[dict]:
    return [
        {"consent_type": "terms_of_service"},
        {"consent_type": "data_processing"},
        {"consent_type": "research_anonymized"},
    ]


async def _register(
    client: AsyncClient,
    *,
    email: str = "test@example.com",
    password: str = "secret-password",
    guest_id: str | None = None,
    consents: list[dict] | None = None,
) -> dict:
    """Хелпер: регистрация и возврат body."""
    payload: dict = {
        "email": email,
        "password": password,
        "consents": consents if consents is not None else _full_consents(),
    }
    if guest_id:
        payload["guest_id"] = guest_id
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


# ============================================================================
# REGISTER
# ============================================================================


class TestRegister:
    async def test_basic_success(self, client: AsyncClient) -> None:
        response = await client.post("/api/auth/register", json={
            "email": "alice@example.com",
            "password": "strongpassword",
            "consents": _full_consents(),
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["user"]["email"] == "alice@example.com"
        assert data["user"]["subscription_tier"] == "free"
        assert data["user"]["is_verified"] is True
        # Cookies должны быть выставлены
        assert "kairos_access" in response.cookies
        assert "kairos_refresh" in response.cookies

    async def test_duplicate_email(self, client: AsyncClient) -> None:
        await _register(client, email="dup@example.com")
        response = await client.post("/api/auth/register", json={
            "email": "dup@example.com",
            "password": "anotherpass",
            "consents": _full_consents(),
        })
        assert response.status_code == 409

    async def test_missing_consents_fails(self, client: AsyncClient) -> None:
        response = await client.post("/api/auth/register", json={
            "email": "no-consent@example.com",
            "password": "password123",
            # consents = пустой список, нет guest_id
            "consents": [],
        })
        assert response.status_code == 400
        assert "consents" in response.json()["detail"]["message"].lower() if isinstance(
            response.json().get("detail"), dict,
        ) else "consents" in str(response.json()).lower()

    async def test_short_password(self, client: AsyncClient) -> None:
        response = await client.post("/api/auth/register", json={
            "email": "short@example.com",
            "password": "abc",  # < 8 символов
            "consents": _full_consents(),
        })
        # Pydantic min_length=8 → 422
        assert response.status_code == 422

    async def test_with_guest_id_uses_existing_consents(
        self, client: AsyncClient,
    ) -> None:
        """Если consent уже дан как guest — registration не требует new consents."""
        guest_id = str(uuid4())
        # Гость дал согласия
        await client.post("/api/consent", json={
            "guest_id": guest_id,
            "consents": _full_consents(),
        })
        # Регистрация без consents в payload — должна пройти,
        # потому что consents мигрируют от guest_id
        response = await client.post("/api/auth/register", json={
            "email": "guest@example.com",
            "password": "password123",
            "guest_id": guest_id,
            "consents": [],  # пусто — но они уже есть от гостя
        })
        assert response.status_code == 200

    async def test_password_hash_not_in_response(
        self, client: AsyncClient,
    ) -> None:
        data = await _register(client)
        # password_hash не должен попасть в response
        assert "password_hash" not in data["user"]
        assert "password" not in data["user"]


# ============================================================================
# LOGIN
# ============================================================================


class TestLogin:
    async def test_success(self, client: AsyncClient) -> None:
        await _register(client, email="login@example.com", password="mypass123")
        response = await client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "mypass123",
        })
        assert response.status_code == 200
        assert "kairos_access" in response.cookies
        assert "kairos_refresh" in response.cookies

    async def test_wrong_password(self, client: AsyncClient) -> None:
        await _register(client, email="wp@example.com", password="correctpass")
        response = await client.post("/api/auth/login", json={
            "email": "wp@example.com",
            "password": "wrongpass",
        })
        assert response.status_code == 401

    async def test_unknown_email(self, client: AsyncClient) -> None:
        response = await client.post("/api/auth/login", json={
            "email": "ghost@example.com",
            "password": "anypass123",
        })
        assert response.status_code == 401

    async def test_error_message_doesnt_leak_user_existence(
        self, client: AsyncClient,
    ) -> None:
        """Ответ при «нет юзера» и «неправильный пароль» должен совпадать."""
        await _register(client, email="real@example.com", password="rightpass")

        wrong_password = await client.post("/api/auth/login", json={
            "email": "real@example.com", "password": "wrongpass",
        })
        unknown_email = await client.post("/api/auth/login", json={
            "email": "fake@example.com", "password": "anypass123",
        })
        assert wrong_password.status_code == unknown_email.status_code == 401
        # Сообщения должны быть идентичны (не утекает наличие email)
        assert wrong_password.json() == unknown_email.json()


# ============================================================================
# /me
# ============================================================================


class TestMe:
    async def test_authenticated(self, client: AsyncClient) -> None:
        data = await _register(client, email="me@example.com")
        # Cookies автоматически в client
        response = await client.get("/api/auth/me")
        assert response.status_code == 200
        assert response.json()["email"] == "me@example.com"
        assert response.json()["id"] == data["user"]["id"]

    async def test_no_cookies_returns_401(self, client: AsyncClient) -> None:
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    async def test_invalid_cookie_returns_401(self, client: AsyncClient) -> None:
        client.cookies.set("kairos_access", "garbage-not-a-jwt")
        response = await client.get("/api/auth/me")
        assert response.status_code == 401


# ============================================================================
# LOGOUT
# ============================================================================


class TestLogout:
    async def test_clears_cookies(self, client: AsyncClient) -> None:
        await _register(client)
        response = await client.post("/api/auth/logout", json={})
        assert response.status_code == 200
        # Set-Cookie с max_age=0 → browser удалит. Но в httpx cookies остаются
        # пока сервер явно не сказал «удалить». Проверяем что Set-Cookie
        # для удаления был отправлен.
        cookie_header = response.headers.get("set-cookie", "")
        assert "kairos_access" in cookie_header
        assert "kairos_refresh" in cookie_header

    async def test_after_logout_me_fails(
        self, client: AsyncClient,
    ) -> None:
        await _register(client)
        await client.post("/api/auth/logout", json={})
        # Очищаем cookies в client (имитируем поведение браузера)
        client.cookies.clear()
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    async def test_everywhere_revokes_all(self, client: AsyncClient) -> None:
        """logout с everywhere=True должен отозвать все refresh пользователя."""
        await _register(client)

        # Имитируем второе устройство — повторный login
        # (без очистки старых cookies — у нас несколько токенов на одного user'а)
        await client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "secret-password",
        })

        # Logout everywhere
        response = await client.post(
            "/api/auth/logout", json={"everywhere": True},
        )
        assert response.status_code == 200

        # Проверяем что в БД все revoked
        from sqlalchemy import select
        from app.data.models import RefreshToken, User
        async with async_session_factory() as db:
            result = await db.execute(
                select(User).where(User.email == "test@example.com"),
            )
            user = result.scalar_one()
            tokens = await db.execute(
                select(RefreshToken).where(RefreshToken.user_id == user.id),
            )
            tokens_list = list(tokens.scalars().all())
            assert len(tokens_list) >= 1  # были выпущены
            assert all(t.revoked_at is not None for t in tokens_list)


# ============================================================================
# REFRESH
# ============================================================================


class TestRefresh:
    async def test_success(self, client: AsyncClient) -> None:
        await _register(client, email="r@example.com")
        original_access = client.cookies.get("kairos_access")
        original_refresh = client.cookies.get("kairos_refresh")

        response = await client.post("/api/auth/refresh", json={})
        assert response.status_code == 200
        # Получили новые токены (отличаются от старых)
        new_access = client.cookies.get("kairos_access")
        new_refresh = client.cookies.get("kairos_refresh")
        assert new_access != original_access
        assert new_refresh != original_refresh

    async def test_no_refresh_cookie_returns_401(
        self, client: AsyncClient,
    ) -> None:
        response = await client.post("/api/auth/refresh", json={})
        assert response.status_code == 401

    async def test_replay_burns_all_tokens(self, client: AsyncClient) -> None:
        """Использование revoked refresh должно отозвать ВСЕ токены user'а."""
        await _register(client, email="replay@example.com")
        old_refresh = client.cookies.get("kairos_refresh")

        # Первый refresh — успешен, старый revoked
        r1 = await client.post("/api/auth/refresh", json={})
        assert r1.status_code == 200

        # Имитируем replay: руками подставляем старый refresh
        # (как будто украли и используем дважды)
        client.cookies.set("kairos_refresh", old_refresh)
        r2 = await client.post("/api/auth/refresh", json={})
        assert r2.status_code == 401  # revoked → отказ

        # И теперь даже текущий новый refresh должен быть отозван
        # (burn всей цепочки). Проверяем что свежий запрос /me не работает.
        from sqlalchemy import select
        from app.data.models import RefreshToken, User
        async with async_session_factory() as db:
            user = (await db.execute(
                select(User).where(User.email == "replay@example.com"),
            )).scalar_one()
            tokens = (await db.execute(
                select(RefreshToken).where(RefreshToken.user_id == user.id),
            )).scalars().all()
            # Все токены user'а должны быть revoked
            assert all(t.revoked_at is not None for t in tokens)


# ============================================================================
# DELETE ACCOUNT
# ============================================================================


class TestDeleteAccount:
    """DELETE /me теперь = soft-delete с 7-day grace period.

    Реальное удаление выполняется Celery-таском `finalize_pending_deletions`
    (см. test_account_deletion.py).
    """

    async def test_schedules_not_deletes(self, client: AsyncClient) -> None:
        """DELETE /me НЕ удаляет сразу — только ставит deletion_scheduled_at."""
        data = await _register(client, email="delete@example.com")
        user_id = data["user"]["id"]

        response = await client.delete("/api/auth/me")
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert body["grace_days"] == 7
        assert "scheduled_at" in body

        # Юзер ВСЁ ЕЩЁ существует в БД
        from sqlalchemy import select
        from app.data.models import User
        async with async_session_factory() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            assert user is not None
            assert user.deletion_scheduled_at is not None

    async def test_revokes_all_tokens(self, client: AsyncClient) -> None:
        """DELETE /me должен отозвать все refresh-токены (юзер вылетает)."""
        await _register(client, email="dr@example.com")
        await client.delete("/api/auth/me")

        # Cookies очищены
        from sqlalchemy import select
        from app.data.models import RefreshToken, User
        async with async_session_factory() as db:
            user = (await db.execute(
                select(User).where(User.email == "dr@example.com"),
            )).scalar_one()
            tokens = (await db.execute(
                select(RefreshToken).where(RefreshToken.user_id == user.id),
            )).scalars().all()
            assert all(t.revoked_at is not None for t in tokens)

    async def test_unauthenticated_cannot_delete(
        self, client: AsyncClient,
    ) -> None:
        response = await client.delete("/api/auth/me")
        assert response.status_code == 401


class TestCancelDeletion:
    """POST /me/cancel-deletion — отмена в 7-дневное окно."""

    async def test_cancel_after_schedule(self, client: AsyncClient) -> None:
        """Запланировал → залогинился → отменил."""
        await _register(client, email="cancel@example.com", password="abcd1234")

        # Schedule deletion
        await client.delete("/api/auth/me")

        # После schedule токены отозваны → нужно перелогиниться
        client.cookies.clear()
        login_resp = await client.post("/api/auth/login", json={
            "email": "cancel@example.com",
            "password": "abcd1234",
        })
        assert login_resp.status_code == 200
        # В UserResponse должен быть deletion_scheduled_at
        assert login_resp.json()["user"]["deletion_scheduled_at"] is not None

        # Cancel
        cancel_resp = await client.post("/api/auth/me/cancel-deletion")
        assert cancel_resp.status_code == 200
        body = cancel_resp.json()
        assert body["ok"] is True
        assert body["was_scheduled"] is True

        # Теперь /me показывает deletion_scheduled_at = None
        me = await client.get("/api/auth/me")
        assert me.json()["deletion_scheduled_at"] is None

    async def test_cancel_when_not_scheduled_is_ok(
        self, client: AsyncClient,
    ) -> None:
        """Идемпотентно: отмена когда удаления нет — тихий ok."""
        await _register(client, email="never@example.com")
        response = await client.post("/api/auth/me/cancel-deletion")
        assert response.status_code == 200
        assert response.json()["was_scheduled"] is False

    async def test_cancel_unauthenticated(self, client: AsyncClient) -> None:
        response = await client.post("/api/auth/me/cancel-deletion")
        assert response.status_code == 401


class TestPendingDeletionBlocksChat:
    """Если у user стоит deletion_scheduled_at — /api/chat блокируется."""

    async def test_chat_blocked_with_403(self, client: AsyncClient) -> None:
        await _register(client, email="block@example.com", password="abcd1234")
        await client.delete("/api/auth/me")

        # Перелогиниваемся
        client.cookies.clear()
        await client.post("/api/auth/login", json={
            "email": "block@example.com",
            "password": "abcd1234",
        })

        # Попытка послать сообщение
        from unittest.mock import AsyncMock, patch
        from app.core.llm.base import LLMResponse, UsageStats

        with patch(
            "app.core.llm.openai_compat.OpenAICompatProvider.generate",
            new=AsyncMock(return_value=LLMResponse(
                text="ok", usage=UsageStats(), response_time_ms=1.0,
            )),
        ):
            response = await client.post("/api/chat", json={"message": "хей"})

        assert response.status_code == 403
        # detail может быть в structured-формате или обёрнут middleware'ом
        body = response.json()
        # Ищем "account_pending_deletion" в любом виде
        assert "pending_deletion" in str(body) or "удаление" in str(body)

    async def test_chat_works_after_cancellation(
        self, client: AsyncClient,
    ) -> None:
        """После cancel-deletion чат снова работает."""
        await _register(client, email="restored@example.com", password="abcd1234")
        await client.delete("/api/auth/me")

        client.cookies.clear()
        await client.post("/api/auth/login", json={
            "email": "restored@example.com",
            "password": "abcd1234",
        })

        # Отменяем
        await client.post("/api/auth/me/cancel-deletion")

        # Чат должен работать
        from unittest.mock import AsyncMock, patch
        from app.core.llm.base import LLMResponse, UsageStats
        import json as json_mod

        analyzer_json = json_mod.dumps({
            "risk_level": "normal",
            "dominant_emotion": "нейтрально",
            "secondary_emotions": [],
            "theme": "general",
            "hidden_signals": [],
            "open_questions": [],
            "what_user_needs": "выслушать",
            "trust_level": 0.7,
            "folder_hints": [],
            "inner_monologue": "ok",
        }, ensure_ascii=False)

        responses = iter([
            LLMResponse(
                text=analyzer_json, usage=UsageStats(), response_time_ms=1.0,
            ),
            LLMResponse(text="привет", usage=UsageStats(), response_time_ms=1.0),
        ])
        # Подменяем Redis на fakeredis
        import fakeredis.aioredis as fakeredis
        fake = fakeredis.FakeRedis()

        with patch(
            "app.core.llm.openai_compat.OpenAICompatProvider.generate",
            new=AsyncMock(side_effect=lambda *a, **k: next(responses)),
        ), patch(
            "app.core.perception.redis_client.get_redis",
            return_value=fake,
        ):
            response = await client.post("/api/chat", json={"message": "хей"})

        assert response.status_code == 200
