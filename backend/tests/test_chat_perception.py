"""Интеграционные тесты /api/chat при включённом use_perception_layer.

LLM мокается ДВАЖДЫ (анализатор + основной), потому что новая ветка
делает два последовательных вызова.
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, patch

import fakeredis.aioredis as fakeredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# В тестах используем отдельный файл SQLite — НЕ трогаем dev-БД.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_chat_perception.db"
os.environ["LLM_API_KEY"] = "test-key"
os.environ["LLM_MODEL"] = "test-model"
# USE_PERCEPTION_LAYER подменяется через monkeypatch ниже,
# чтобы перебить кешированное settings, если другой тест-файл импортировал
# settings раньше.

from app.core.llm.base import LLMResponse, UsageStats
from app.data.database import create_all_tables, drop_all_tables


def _llm(text: str) -> LLMResponse:
    return LLMResponse(
        text=text,
        usage=UsageStats(prompt_tokens=100, completion_tokens=50, total_tokens=150),
        response_time_ms=42.0,
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


@pytest.fixture(autouse=True)
def enable_perception_flag(monkeypatch):
    """Принудительно включаем флаг для всех тестов файла.

    Это критично: обычный os.environ не сработает, если settings уже
    закеширован после импорта другим тестовым файлом.
    """
    from app.config import settings
    monkeypatch.setattr(settings, "use_perception_layer", True)


@pytest_asyncio.fixture
async def app_with_db() -> AsyncIterator[Any]:
    """Свежая БД на каждый тест."""
    await drop_all_tables()
    await create_all_tables()
    from app.main import app
    yield app
    await drop_all_tables()


@pytest_asyncio.fixture
async def client(app_with_db, monkeypatch) -> AsyncIterator[AsyncClient]:
    """HTTP-клиент с подменой Redis на fakeredis."""
    fake = fakeredis.FakeRedis()
    # Подменяем get_redis() на fakeredis-обёртку.
    # Импорт делается ВНУТРИ chat.py через
    # `from app.core.perception.redis_client import get_redis`,
    # поэтому патчим оба места — на всякий.
    monkeypatch.setattr(
        "app.core.perception.redis_client.get_redis",
        lambda: fake,
    )
    transport = ASGITransport(app=app_with_db)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await fake.aclose()


def _two_step_mock(analyzer_text: str, main_text: str):
    """Двухступенчатый мок: первый вызов = analyzer, второй = main."""
    calls = {"n": 0}

    async def gen(*args, **kwargs):
        calls["n"] += 1
        return _llm(analyzer_text if calls["n"] == 1 else main_text)

    return AsyncMock(side_effect=gen), calls


# ============================================================================
# Тесты
# ============================================================================


async def test_chat_normal_message_with_perception(client: AsyncClient):
    """Обычное сообщение через PerceptionPipeline → 2 LLM-вызова, normal."""
    mock, calls = _two_step_mock(
        _analyzer_json("normal"),
        "Слышу тебя. Расскажи, что у тебя сейчас.",
    )
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=mock,
    ):
        resp = await client.post("/api/chat", json={"message": "привет"})

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert calls["n"] == 2  # analyzer + main
    assert data["crisis_level"] == "normal"
    assert "Слышу тебя" in data["reply"]
    assert data["branch"] is None  # в новой ветке branch не используется


async def test_chat_immediate_crisis_with_perception(client: AsyncClient):
    """immediate из анализатора → crisis_contacts заполнены."""
    mock, _ = _two_step_mock(
        _analyzer_json("immediate"),
        "Я слышу тебя. Это очень тяжело.",
    )
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=mock,
    ):
        resp = await client.post(
            "/api/chat",
            json={"message": "хочу умереть", "age_group": "adult"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["crisis_level"] == "immediate"
    assert len(data["crisis_contacts"]) > 0
    phones = [c["phone"] for c in data["crisis_contacts"]]
    assert "112" in phones


async def test_chat_perception_pipeline_failure_fallback(client: AsyncClient):
    """Если PerceptionPipeline упал — отвечаем fallback-текстом, НЕ 500."""
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(side_effect=RuntimeError("LLM down")),
    ):
        resp = await client.post("/api/chat", json={"message": "привет"})

    assert resp.status_code == 200, resp.text
    data = resp.json()
    # Fallback-текст для нового слоя
    assert "не могу" in data["reply"].lower()
    # crisis_level откатывается на normal (мы не знаем без анализа)
    assert data["crisis_level"] == "normal"


async def test_chat_perception_persists_session(client: AsyncClient):
    """Два сообщения с одним session_id → одна сессия в БД."""
    mock = AsyncMock(side_effect=lambda *a, **k: _llm(_analyzer_json()))

    async def gen(*args, **kwargs):
        # alternate analyzer/main
        gen.n = getattr(gen, "n", 0) + 1
        if gen.n % 2 == 1:
            return _llm(_analyzer_json("normal"))
        return _llm("ok")

    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(side_effect=gen),
    ):
        r1 = await client.post("/api/chat", json={"message": "привет"})
        sid = r1.json()["session_id"]
        r2 = await client.post(
            "/api/chat",
            json={"message": "ещё", "session_id": sid},
        )

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["session_id"] == sid
