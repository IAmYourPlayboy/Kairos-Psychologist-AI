"""Тесты API согласий (POST /api/consent, GET /api/consent).

Проверяем:
- POST принимает 3 согласия и пишет их в БД с метаданными.
- GET возвращает список согласий и флаг has_all_required.
- has_all_required=True только если все 3 типа активны.
- IP и User-Agent сохраняются.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_consent_api.db"
os.environ["LLM_API_KEY"] = "test-key"

from app.data.database import (
    async_session_factory,
    create_all_tables,
    drop_all_tables,
)


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Чистая БД для каждого теста."""
    await drop_all_tables()
    await create_all_tables()
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await drop_all_tables()


# ============================================================================
# POST /api/consent
# ============================================================================


async def test_submit_three_consents(client: AsyncClient) -> None:
    """Базовый сценарий: три согласия, всё ок."""
    guest_id = str(uuid4())
    response = await client.post(
        "/api/consent",
        json={
            "guest_id": guest_id,
            "consents": [
                {"consent_type": "terms_of_service"},
                {"consent_type": "data_processing"},
                {"consent_type": "research_anonymized"},
            ],
        },
        headers={"User-Agent": "Mozilla/5.0 TestBrowser"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["accepted_count"] == 3
    assert len(data["consent_ids"]) == 3


async def test_submit_without_guest_id_fails(client: AsyncClient) -> None:
    """Без guest_id (и user_id) — 400."""
    response = await client.post(
        "/api/consent",
        json={
            "consents": [{"consent_type": "terms_of_service"}],
        },
    )
    assert response.status_code == 400


async def test_submit_with_unknown_consent_type_fails(client: AsyncClient) -> None:
    """Неизвестный тип согласия — Pydantic валидация → 422."""
    response = await client.post(
        "/api/consent",
        json={
            "guest_id": str(uuid4()),
            "consents": [{"consent_type": "totally_made_up_type"}],
        },
    )
    assert response.status_code == 422


async def test_submit_records_metadata(client: AsyncClient) -> None:
    """IP и User-Agent должны быть записаны."""
    guest_id = str(uuid4())
    await client.post(
        "/api/consent",
        json={
            "guest_id": guest_id,
            "consents": [{"consent_type": "terms_of_service"}],
        },
        headers={
            "User-Agent": "MyTestBrowser/1.0",
            "X-Forwarded-For": "1.2.3.4, 5.6.7.8",
        },
    )

    from sqlalchemy import select
    from app.data.models import UserConsent

    async with async_session_factory() as db:
        result = await db.execute(
            select(UserConsent).where(UserConsent.guest_id == guest_id)
        )
        consent = result.scalar_one()
        assert consent.ip_address == "1.2.3.4"
        assert "MyTestBrowser" in consent.user_agent
        assert consent.consent_type == "terms_of_service"
        assert consent.document_version == "1.0"


# ============================================================================
# GET /api/consent
# ============================================================================


async def test_get_consents_returns_all(client: AsyncClient) -> None:
    """GET /api/consent должен вернуть все согласия пользователя."""
    guest_id = str(uuid4())
    await client.post(
        "/api/consent",
        json={
            "guest_id": guest_id,
            "consents": [
                {"consent_type": "terms_of_service"},
                {"consent_type": "data_processing"},
                {"consent_type": "research_anonymized"},
            ],
        },
    )

    response = await client.get(f"/api/consent?guest_id={guest_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["consents"]) == 3
    assert data["has_all_required"] is True


async def test_get_consents_partial_required_false(client: AsyncClient) -> None:
    """Если только 2 из 3 — has_all_required=False."""
    guest_id = str(uuid4())
    await client.post(
        "/api/consent",
        json={
            "guest_id": guest_id,
            "consents": [
                {"consent_type": "terms_of_service"},
                {"consent_type": "data_processing"},
                # research_anonymized не дано
            ],
        },
    )

    response = await client.get(f"/api/consent?guest_id={guest_id}")
    data = response.json()
    assert len(data["consents"]) == 2
    assert data["has_all_required"] is False


async def test_get_consents_unknown_guest_returns_empty(
    client: AsyncClient,
) -> None:
    """Гость, которого нет в БД — пустой список."""
    response = await client.get(f"/api/consent?guest_id={uuid4()}")
    data = response.json()
    assert data["consents"] == []
    assert data["has_all_required"] is False


async def test_get_consents_no_guest_id_returns_empty(
    client: AsyncClient,
) -> None:
    """Без guest_id — пустой список (а не ошибка)."""
    response = await client.get("/api/consent")
    data = response.json()
    assert data["consents"] == []
    assert data["has_all_required"] is False
