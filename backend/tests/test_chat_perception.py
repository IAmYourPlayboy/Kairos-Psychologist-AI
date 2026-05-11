"""Интеграционные тесты /api/chat (новый слой восприятия).

LLM мокается ДВАЖДЫ (анализатор + основной), потому что цикл
делает два последовательных вызова: PerceptionPipeline сначала зовёт
MessageAnalyzer, потом основную LLM.
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


async def test_chat_perception_json_persisted_with_all_fields(
    client: AsyncClient,
):
    """B4: проверяем, что в БД пишется ПОЛНЫЙ PerceptionReport, не выборка.

    Это база для калибровки регулятора (PROGRESS.md строки 1367-1449)
    и для будущей LoRA: если в perception_json не хватит каких-то полей,
    мы потеряем сигнал.
    """
    import json as json_module

    custom_analyzer = json_module.dumps(
        {
            "risk_level": "elevated",
            "dominant_emotion": "тревога",
            "secondary_emotions": ["усталость", "сомнение"],
            "theme": "work/burnout",
            "hidden_signals": ["не спит", "не ест"],
            "open_questions": ["сколько это длится?"],
            "what_user_needs": "выслушать без советов",
            "trust_level": 0.55,
            "folder_hints": ["work/career", "health/sleep"],
            "inner_monologue": "Видно эмоциональное выгорание.",
        },
        ensure_ascii=False,
    )
    mock, _ = _two_step_mock(custom_analyzer, "Слышу тебя.")
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=mock,
    ):
        resp = await client.post(
            "/api/chat",
            json={"message": "не сплю уже неделю, всё валится"},
        )

    assert resp.status_code == 200
    sid = resp.json()["session_id"]

    # Прочитаем из БД и убедимся, что все поля сохранились
    from sqlalchemy import select
    from app.data.database import async_session_factory
    from app.data.models import Message

    async with async_session_factory() as db:
        result = await db.execute(
            select(Message)
            .where(Message.session_id == sid)
            .where(Message.role == "user"),
        )
        user_msg = result.scalar_one()
        assert user_msg.perception_json is not None

        report = json_module.loads(user_msg.perception_json)
        # Все 11 полей должны быть на месте
        assert report["risk_level"] == "elevated"
        assert report["dominant_emotion"] == "тревога"
        assert report["secondary_emotions"] == ["усталость", "сомнение"]
        assert report["theme"] == "work/burnout"
        assert report["hidden_signals"] == ["не спит", "не ест"]
        assert report["open_questions"] == ["сколько это длится?"]
        assert report["what_user_needs"] == "выслушать без советов"
        assert report["trust_level"] == 0.55
        assert report["folder_hints"] == ["work/career", "health/sleep"]
        assert "выгорание" in report["inner_monologue"]


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


# ============================================================================
# Регрессия: сессия залогиненного пользователя должна хранить user_id
# (баг Сессии 27: _get_or_create_session не принимал user_id → Dossier
# не работал для залогиненных)
# ============================================================================


async def test_chat_session_stores_user_id_for_logged_in_user(
    client: AsyncClient,
):
    """Залогиненный пользователь → новая сессия пишется с user_id в БД.

    Без этого фикса сессия создавалась с user_id=None, pipeline считал
    пользователя гостем, Dossier/ReflectionAgent не включались.
    """
    # Регистрация кладёт cookies в client → следующий /api/chat уже залогинен
    reg = await client.post(
        "/api/auth/register",
        json={
            "email": "continuity@example.com",
            "password": "test-password-123",
            "consents": [
                {"consent_type": "terms_of_service", "granted": True},
                {"consent_type": "data_processing", "granted": True},
                {"consent_type": "research_anonymized", "granted": True},
            ],
        },
    )
    assert reg.status_code == 200, reg.text
    user_id = reg.json()["user"]["id"]

    mock, _ = _two_step_mock(
        _analyzer_json("normal"),
        "ок",
    )
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=mock,
    ):
        resp = await client.post("/api/chat", json={"message": "привет"})

    assert resp.status_code == 200
    sid = resp.json()["session_id"]

    from sqlalchemy import select
    from app.data.database import async_session_factory
    from app.data.models import ChatSession as CS

    async with async_session_factory() as db:
        row = (await db.execute(select(CS).where(CS.id == sid))).scalar_one()
        assert row.user_id == user_id, (
            f"сессия залогиненного пользователя должна иметь user_id={user_id}, "
            f"а не {row.user_id!r}"
        )


async def test_chat_attaches_existing_guest_session_on_login(
    client: AsyncClient,
):
    """Гостевая сессия → юзер логинится → следующий /api/chat привязывает
    её к user_id, не создавая новую.

    Это покрывает случай, когда пользователь начал разговор гостем, затем
    зарегистрировался, и отправил ещё одно сообщение в ту же сессию до того,
    как фронт вызвал /api/sessions/migrate.
    """
    # Шаг 1: гостевое сообщение (без cookies)
    mock1, _ = _two_step_mock(_analyzer_json("normal"), "ок")
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=mock1,
    ):
        r = await client.post(
            "/api/chat",
            json={
                "message": "привет",
                "guest_id": "11111111-1111-1111-1111-111111111111",
            },
        )
    assert r.status_code == 200
    sid = r.json()["session_id"]

    # Убедимся, что сейчас сессия — гостевая (user_id=None)
    from sqlalchemy import select
    from app.data.database import async_session_factory
    from app.data.models import ChatSession as CS

    async with async_session_factory() as db:
        row = (await db.execute(select(CS).where(CS.id == sid))).scalar_one()
        assert row.user_id is None

    # Шаг 2: регистрация (ставит cookies в client)
    reg = await client.post(
        "/api/auth/register",
        json={
            "email": "attach@example.com",
            "password": "test-password-123",
            "consents": [
                {"consent_type": "terms_of_service", "granted": True},
                {"consent_type": "data_processing", "granted": True},
                {"consent_type": "research_anonymized", "granted": True},
            ],
        },
    )
    assert reg.status_code == 200, reg.text
    user_id = reg.json()["user"]["id"]

    # Шаг 3: следующий /api/chat с той же session_id — должен привязать
    mock2, _ = _two_step_mock(_analyzer_json("normal"), "ок2")
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=mock2,
    ):
        r2 = await client.post(
            "/api/chat",
            json={"message": "ещё", "session_id": sid},
        )
    assert r2.status_code == 200

    async with async_session_factory() as db:
        row = (await db.execute(select(CS).where(CS.id == sid))).scalar_one()
        assert row.user_id == user_id, (
            "существующая гостевая сессия должна быть привязана к "
            f"залогиненному юзеру, а не остаться с user_id={row.user_id!r}"
        )
