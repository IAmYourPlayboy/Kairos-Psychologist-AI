"""E2E-тест: ASQ-positive override risk_level=immediate в /api/chat.

Сценарий:
1. Гость проходит ASQ → результат acute_positive.
2. Следующий /api/chat с этим guest_id, даже на нейтральное сообщение
   и при «normal» от анализатора — должен вернуть crisis_level=immediate.

Это валидирует ADR-1 (единственное rule-based исключение
в post-Сессия-18 пайплайне).
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import fakeredis.aioredis as fakeredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_chat_asq_override.db"
os.environ["LLM_API_KEY"] = "test-key"
os.environ["LLM_MODEL"] = "test-model"

from app.core.llm.base import LLMResponse, UsageStats
from app.data.database import (
    async_session_factory,
    create_all_tables,
    drop_all_tables,
)
from app.data.models import ChatSession


def _llm(text: str) -> LLMResponse:
    return LLMResponse(
        text=text,
        usage=UsageStats(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        response_time_ms=10.0,
    )


def _analyzer_json(risk: str = "normal") -> str:
    return json.dumps(
        {
            "risk_level": risk,
            "dominant_emotion": "нейтрально",
            "secondary_emotions": [],
            "theme": "general",
            "hidden_signals": [],
            "open_questions": [],
            "what_user_needs": "выслушать",
            "trust_level": 0.7,
            "folder_hints": [],
            "inner_monologue": "ок",
        },
        ensure_ascii=False,
    )


def _two_step_mock(analyzer_text: str, main_text: str):
    """Двухступенчатый мок: первый вызов = analyzer, второй = main LLM."""
    calls = {"n": 0}

    async def gen(*args, **kwargs):
        calls["n"] += 1
        return _llm(analyzer_text if calls["n"] == 1 else main_text)

    return AsyncMock(side_effect=gen), calls


@pytest_asyncio.fixture
async def app_with_db() -> AsyncIterator[Any]:
    await drop_all_tables()
    await create_all_tables()
    from app.main import app
    yield app
    await drop_all_tables()


@pytest_asyncio.fixture
async def client(app_with_db, monkeypatch) -> AsyncIterator[AsyncClient]:
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(
        "app.core.perception.redis_client.get_redis",
        lambda: fake,
    )
    monkeypatch.setattr(
        "app.api.screening.get_redis",
        lambda: fake,
    )
    transport = ASGITransport(app=app_with_db)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await fake.aclose()


# ============================================================================
# Тест: ASQ-positive у гостя → следующий /api/chat returns immediate
# ============================================================================


async def test_asq_positive_override_forces_immediate_in_chat(
    client: AsyncClient,
):
    """После сохранения ASQ-positive у guest, любой /api/chat с этим
    guest_id возвращает crisis_level=immediate, даже на нейтральное
    сообщение и normal от анализатора.
    """
    guest_id = str(uuid4())
    session_id = str(uuid4())

    # Создаём ChatSession с guest_id (бекенд не создаёт session
    # без вызова /api/chat, но screening требует существующую сессию)
    async with async_session_factory() as db:
        db.add(ChatSession(id=session_id, guest_id=guest_id))
        await db.commit()

    # === Шаг 1: пользователь проходит ASQ → acute_positive ===
    asq_resp = await client.post(
        "/api/screening/asq",
        json={
            "session_id": session_id,
            "answers": {
                "1": "yes", "2": "no", "3": "yes", "4": "no", "5": "yes",
            },
        },
    )
    assert asq_resp.status_code == 200, asq_resp.text
    assert asq_resp.json()["interpretation"] == "acute_positive"
    assert asq_resp.json()["is_positive"] is True

    # === Шаг 2: следующий /api/chat с этим guest_id ===
    # Анализатор намеренно возвращает risk_level="normal" — но override
    # должен переписать его в "immediate".
    mock, calls = _two_step_mock(
        _analyzer_json("normal"),  # анализатор говорит "normal"
        "Я слышу тебя.",
    )
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=mock,
    ):
        chat_resp = await client.post(
            "/api/chat",
            json={
                "message": "привет, как дела?",  # нейтральное сообщение
                "session_id": session_id,
                "guest_id": guest_id,
            },
        )

    assert chat_resp.status_code == 200, chat_resp.text
    data = chat_resp.json()

    # Override должен сработать: crisis_level=immediate несмотря на normal
    assert data["crisis_level"] == "immediate", (
        f"Expected immediate due to ASQ-positive override, got {data['crisis_level']}"
    )
    # И, как следствие, кризисные контакты должны быть отданы
    assert len(data["crisis_contacts"]) > 0
    # Анализатор всё ещё вызывался (override не отменяет analysis)
    assert calls["n"] == 2  # analyzer + main


async def test_asq_negative_does_not_override(client: AsyncClient):
    """ASQ negative НЕ должен повышать risk_level — override только
    при positive интерпретациях."""
    guest_id = str(uuid4())
    session_id = str(uuid4())

    async with async_session_factory() as db:
        db.add(ChatSession(id=session_id, guest_id=guest_id))
        await db.commit()

    # Negative
    asq_resp = await client.post(
        "/api/screening/asq",
        json={
            "session_id": session_id,
            "answers": {"1": "no", "2": "no", "3": "no", "4": "no"},
        },
    )
    assert asq_resp.json()["interpretation"] == "negative"

    mock, _ = _two_step_mock(
        _analyzer_json("normal"),
        "ок",
    )
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=mock,
    ):
        chat_resp = await client.post(
            "/api/chat",
            json={
                "message": "привет",
                "session_id": session_id,
                "guest_id": guest_id,
            },
        )

    assert chat_resp.status_code == 200
    # crisis_level остаётся normal
    assert chat_resp.json()["crisis_level"] == "normal"


async def test_asq_positive_for_other_guest_does_not_override(
    client: AsyncClient,
):
    """ASQ-positive у одного guest не должен повышать risk_level
    у другого guest."""
    guest_a = str(uuid4())
    guest_b = str(uuid4())
    session_a = str(uuid4())
    session_b = str(uuid4())

    async with async_session_factory() as db:
        db.add(ChatSession(id=session_a, guest_id=guest_a))
        db.add(ChatSession(id=session_b, guest_id=guest_b))
        await db.commit()

    # Positive у A
    await client.post(
        "/api/screening/asq",
        json={
            "session_id": session_a,
            "answers": {
                "1": "yes", "2": "no", "3": "no", "4": "no", "5": "yes",
            },
        },
    )

    # Чат у B — override НЕ должен сработать
    mock, _ = _two_step_mock(_analyzer_json("normal"), "ок")
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=mock,
    ):
        chat_resp = await client.post(
            "/api/chat",
            json={
                "message": "привет",
                "session_id": session_b,
                "guest_id": guest_b,
            },
        )

    assert chat_resp.json()["crisis_level"] == "normal"
