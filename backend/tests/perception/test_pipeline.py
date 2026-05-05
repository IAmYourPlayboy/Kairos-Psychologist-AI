"""Тесты PerceptionPipeline — оркестратора всего цикла одного сообщения.

Здесь критично: проверяем последовательность вызовов и правильное
использование результатов между компонентами.
"""

from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import fakeredis.aioredis as fakeredis
import pytest
import pytest_asyncio

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_pipeline.db"
os.environ["LLM_API_KEY"] = "test-key"

from app.core.llm.base import LLMResponse, UsageStats
from app.core.perception.pipeline import PerceptionPipeline, PipelineResult
from app.data.database import (
    async_session_factory,
    create_all_tables,
    drop_all_tables,
)
from app.data.models import ChatSession, User


@pytest_asyncio.fixture
async def db_with_user():
    await drop_all_tables()
    await create_all_tables()
    user_id = str(uuid4())
    session_id = str(uuid4())
    async with async_session_factory() as db:
        user = User(id=user_id, email="t@e.com")
        db.add(user)
        session = ChatSession(id=session_id, user_id=user_id)
        db.add(session)
        await db.commit()
    yield {"user_id": user_id, "session_id": session_id}
    await drop_all_tables()


@pytest_asyncio.fixture
async def fake_redis():
    r = fakeredis.FakeRedis()
    yield r
    await r.aclose()


def _llm(text: str, p_in: int = 100, p_out: int = 50) -> LLMResponse:
    return LLMResponse(
        text=text,
        usage=UsageStats(
            prompt_tokens=p_in, completion_tokens=p_out,
            total_tokens=p_in + p_out,
        ),
        response_time_ms=42.0,
    )


def _analyzer_response_json(risk: str = "elevated") -> str:
    return json.dumps(
        {
            "risk_level": risk,
            "dominant_emotion": "страх",
            "secondary_emotions": [],
            "theme": "school_peers/bullying",
            "hidden_signals": [],
            "open_questions": [],
            "what_user_needs": "выслушать",
            "trust_level": 0.85,
            "folder_hints": [],
            "inner_monologue": "не торопить",
        },
        ensure_ascii=False,
    )


async def test_pipeline_full_cycle(db_with_user, fake_redis):
    """Полный цикл: analyzer → mood update → prompt build → main LLM."""
    call_count = {"n": 0}

    async def fake_generate(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # Первый вызов = анализатор
            return _llm(_analyzer_response_json("elevated"))
        # Второй вызов = основной ответ
        return _llm("слышу тебя, расскажи подробнее")

    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(side_effect=fake_generate),
    ):
        async with async_session_factory() as db:
            pipeline = PerceptionPipeline(db=db, redis_client=fake_redis)
            result: PipelineResult = await pipeline.process_message(
                user_id=db_with_user["user_id"],
                session_id=db_with_user["session_id"],
                user_message="опять туалет, страшно",
                history=[],
            )

    # Один вызов на анализатор + один на основной ответ
    assert call_count["n"] == 2
    assert result.report.risk_level == "elevated"
    assert "слышу тебя" in result.reply
    # mood обновился по elevated risk
    assert result.mood.alertness > 0.5


async def test_pipeline_for_guest_no_dossier(db_with_user, fake_redis):
    """Гость (user_id=None) → досье недоступно, всё работает."""
    call_count = {"n": 0}

    async def fake_generate(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _llm(_analyzer_response_json("normal"))
        return _llm("привет")

    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(side_effect=fake_generate),
    ):
        async with async_session_factory() as db:
            pipeline = PerceptionPipeline(db=db, redis_client=fake_redis)
            result = await pipeline.process_message(
                user_id=None,
                session_id=db_with_user["session_id"],
                user_message="привет",
                history=[],
            )

    assert call_count["n"] == 2
    assert result.reply == "привет"


async def test_pipeline_analyzer_failure_propagates(db_with_user, fake_redis):
    """Если анализатор упал — основной ответ не должен генерироваться."""
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(side_effect=RuntimeError("LLM down")),
    ):
        async with async_session_factory() as db:
            pipeline = PerceptionPipeline(db=db, redis_client=fake_redis)
            with pytest.raises(RuntimeError):
                await pipeline.process_message(
                    user_id=db_with_user["user_id"],
                    session_id=db_with_user["session_id"],
                    user_message="привет",
                    history=[],
                )


async def test_pipeline_mood_persisted_between_calls(
    db_with_user, fake_redis,
):
    """Mood накапливается в Redis: после immediate alertness сохраняется."""
    # Чередуем: чётные вызовы — analyzer, нечётные — main reply.
    counter = {"n": 0}

    async def fake_generate(*args, **kwargs):
        counter["n"] += 1
        # 1 — analyzer, 2 — main, 3 — analyzer, 4 — main, ...
        if counter["n"] % 2 == 1:
            return _llm(_analyzer_response_json("immediate"))
        return _llm("ok-reply")

    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(side_effect=fake_generate),
    ):
        async with async_session_factory() as db:
            pipeline = PerceptionPipeline(db=db, redis_client=fake_redis)
            r1 = await pipeline.process_message(
                user_id=db_with_user["user_id"],
                session_id=db_with_user["session_id"],
                user_message="хочу умереть",
                history=[],
            )
            assert r1.mood.alertness >= 0.85

    # Новая сессия БД, но Mood в Redis — тот же
    async with async_session_factory() as db:
        from app.core.perception.mood import MoodService
        mood_service = MoodService(fake_redis)
        mood_now = await mood_service.get(db_with_user["session_id"])
        # alertness сохранился между запросами
        assert mood_now.alertness >= 0.85
