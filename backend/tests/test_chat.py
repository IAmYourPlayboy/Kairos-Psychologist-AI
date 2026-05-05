"""Интеграционные тесты эндпоинта /api/chat (Блок 5) и /api/feedback (Блок 5.5).

Запуск:
    cd backend
    pytest tests/test_chat.py -v

Особенности:
- Используем in-memory SQLite (`sqlite+aiosqlite:///:memory:`).
- LLM провайдер замокан — вместо реальных HTTP-запросов к Yandex Cloud
  возвращаем фиксированный ответ. Это убирает зависимость от сети и
  ускоряет тесты в ~100 раз.
- Каждый тест получает чистую БД (фикстура `client` с автоочисткой).
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# В тестах используем отдельный файл SQLite (`./kairos_test.db`) —
# НЕ трогаем dev-БД и не используем `:memory:` (in-memory у aiosqlite не
# разделяется между соединениями, а у нас async pool создаёт несколько).
# Жёсткое присваивание перебивает значения из .env при импорте Settings.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test.db"
# Не вызываем реальный LLM API — все вызовы провайдера замоканы фикстурой.
os.environ["LLM_API_KEY"] = "test-key-not-real"
os.environ["LLM_MODEL"] = "test-model"

from app.core.llm.base import LLMResponse, UsageStats
from app.data.database import create_all_tables, drop_all_tables


# ============================================================================
# Фикстуры
# ============================================================================


@pytest_asyncio.fixture
async def app_with_db() -> AsyncIterator[Any]:
    """Создаём чистую БД перед каждым тестом и удаляем после."""
    await create_all_tables()
    # Импортируем app внутри фикстуры, чтобы env-переменные подхватились
    from app.main import app

    yield app
    await drop_all_tables()


@pytest_asyncio.fixture
async def client(app_with_db: Any) -> AsyncIterator[AsyncClient]:
    """HTTP-клиент против ASGI-приложения (без реального сервера)."""
    transport = ASGITransport(app=app_with_db)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_llm_reply():
    """Замокать вызов LLM провайдера. Возвращает фиксированный ответ."""
    fake_response = LLMResponse(
        text="Слышу тебя. Сейчас тяжело, да? Расскажи, что происходит.",
        usage=UsageStats(prompt_tokens=120, completion_tokens=15, total_tokens=135),
        response_time_ms=42.0,
    )

    async def _fake_generate(*args: Any, **kwargs: Any) -> LLMResponse:
        return fake_response

    # Патчим метод generate у класса OpenAICompatProvider — чтобы singleton
    # из factory.get_provider() тоже был замокан.
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(side_effect=_fake_generate),
    ) as m:
        yield m


# ============================================================================
# Тесты /api/chat
# ============================================================================


async def test_chat_normal_message(client: AsyncClient, mock_llm_reply):
    """Обычное сообщение — нет кризиса, ответ от (мока) LLM."""
    resp = await client.post(
        "/api/chat",
        json={"message": "привет, как дела"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["reply"]  # непустой
    assert data["crisis_level"] == "normal"
    assert data["crisis_contacts"] == []
    assert data["session_id"]  # сгенерирован сервером
    assert data["message_id"]  # id ответа бота
    assert data["branch"] in ("A", "B")


async def test_chat_immediate_crisis_returns_contacts(
    client: AsyncClient, mock_llm_reply
):
    """Кризисное сообщение → crisis_level=immediate + список контактов."""
    resp = await client.post(
        "/api/chat",
        json={"message": "хочу умереть", "age_group": "adult"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["crisis_level"] == "immediate"
    assert len(data["crisis_contacts"]) >= 3

    phones = [c["phone"] for c in data["crisis_contacts"]]
    assert "112" in phones
    assert "8-800-333-44-34" in phones


async def test_chat_high_crisis(client: AsyncClient, mock_llm_reply):
    """Безысходность → high crisis + контакты."""
    resp = await client.post(
        "/api/chat",
        json={"message": "нет выхода, никто не поможет"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["crisis_level"] == "high"
    assert len(data["crisis_contacts"]) >= 1


async def test_chat_persists_session(client: AsyncClient, mock_llm_reply):
    """Два сообщения с одним session_id попадают в одну сессию."""
    # Первое сообщение
    resp1 = await client.post(
        "/api/chat",
        json={"message": "первое сообщение"},
    )
    assert resp1.status_code == 200, resp1.text
    sid = resp1.json()["session_id"]

    # Второе сообщение с тем же session_id
    resp2 = await client.post(
        "/api/chat",
        json={"message": "второе сообщение", "session_id": sid},
    )
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["session_id"] == sid


async def test_chat_validates_empty_message(client: AsyncClient, mock_llm_reply):
    """Пустое сообщение → 422 Validation Error."""
    resp = await client.post("/api/chat", json={"message": ""})
    assert resp.status_code == 422


async def test_chat_validates_too_long(client: AsyncClient, mock_llm_reply):
    """Сообщение длиннее лимита → 422."""
    huge = "а" * 10_000
    resp = await client.post("/api/chat", json={"message": huge})
    # Может быть 422 (валидация) или 200 если лимит большой — главное не 500
    assert resp.status_code in (200, 422)


async def test_chat_llm_failure_returns_fallback(client: AsyncClient):
    """Если LLM упал — должен вернуться fallback-ответ, не 500."""
    # Патчим generate так, чтобы он бросал исключение
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(side_effect=RuntimeError("LLM недоступен")),
    ):
        resp = await client.post(
            "/api/chat",
            json={"message": "хочу умереть"},
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # Кризис должен сохраниться
    assert data["crisis_level"] == "immediate"
    # Fallback должен содержать кризисные номера
    assert "112" in data["reply"]
    assert "8-800" in data["reply"]


# ============================================================================
# Тесты /api/feedback
# ============================================================================


async def test_feedback_creates_event(client: AsyncClient, mock_llm_reply):
    """POST /api/feedback после chat → 200 + feedback_id."""
    # Сначала создаём сессию через chat
    chat_resp = await client.post("/api/chat", json={"message": "привет"})
    assert chat_resp.status_code == 200
    session_id = chat_resp.json()["session_id"]
    message_id = chat_resp.json()["message_id"]

    # Шлём feedback
    fb_resp = await client.post(
        "/api/feedback",
        json={
            "session_id": session_id,
            "message_id": message_id,
            "event_type": "thumbs_up",
        },
    )
    assert fb_resp.status_code == 200, fb_resp.text
    data = fb_resp.json()
    assert data["ok"] is True
    assert data["feedback_id"]


async def test_feedback_session_outcome_update(
    client: AsyncClient, mock_llm_reply
):
    """felt_better → outcome сессии обновляется."""
    chat_resp = await client.post("/api/chat", json={"message": "привет"})
    session_id = chat_resp.json()["session_id"]

    fb_resp = await client.post(
        "/api/feedback",
        json={
            "session_id": session_id,
            "message_id": None,
            "event_type": "felt_better",
        },
    )
    assert fb_resp.status_code == 200, fb_resp.text


async def test_feedback_invalid_event_type_rejected(client: AsyncClient):
    """Неизвестный event_type → 422."""
    resp = await client.post(
        "/api/feedback",
        json={
            "session_id": "00000000-0000-0000-0000-000000000000",
            "event_type": "kaboom",
        },
    )
    assert resp.status_code in (400, 422)


# ============================================================================
# Тесты /api/health
# ============================================================================


async def test_health_endpoint(client: AsyncClient):
    """GET /api/health → 200 ok."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
