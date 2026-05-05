"""Тесты ReflectionAgent — полный цикл extract → classify → dedupe → update.

LLM замокан. Проверяем, что:
- Корректно загружаются сообщения после чекпойнта.
- Создаются факты с цитатами.
- При повторе — checkpoint сдвигается, второй прогон ничего не меняет.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest_asyncio

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_reflection.db"
os.environ["LLM_API_KEY"] = "test-key"

from app.core.llm.base import LLMResponse, UsageStats
from app.core.perception.reflection_agent import ReflectionAgent
from app.data.database import (
    async_session_factory,
    create_all_tables,
    drop_all_tables,
)
from app.data.dossier_models import DossierCheckpoint, DossierFact
from app.data.models import ChatSession, Message, User


def _llm(text: str) -> LLMResponse:
    return LLMResponse(
        text=text,
        usage=UsageStats(prompt_tokens=200, completion_tokens=100, total_tokens=300),
        response_time_ms=100.0,
    )


@pytest_asyncio.fixture
async def db_with_messages():
    """Пользователь, сессия, 3 user-сообщения. Чекпойнта НЕТ —
    ReflectionAgent должен обработать всё с нуля.
    """
    await drop_all_tables()
    await create_all_tables()
    user_id = str(uuid4())
    session_id = str(uuid4())
    msg_ids: list[str] = []

    async with async_session_factory() as db:
        user = User(id=user_id, email="t@e.com")
        db.add(user)
        session = ChatSession(id=session_id, user_id=user_id)
        db.add(session)

        for i, text in enumerate([
            "у меня есть младший братишка егор",
            "папа опять напился вчера",
            "я общаюсь с тобой каждый день в 20:00",
        ]):
            mid = str(uuid4())
            msg_ids.append(mid)
            db.add(Message(
                id=mid,
                session_id=session_id,
                role="user",
                content=text,
                server_timestamp=datetime.now(timezone.utc) + timedelta(seconds=i),
            ))
        await db.commit()

    yield {"user_id": user_id, "session_id": session_id, "msg_ids": msg_ids}
    await drop_all_tables()


def _extract_response_for_three_messages(msg_ids: list[str]) -> str:
    """Мок-ответ extract-этапа для 3 сообщений."""
    return json.dumps([
        {
            "summary": "Есть младший брат Егор",
            "candidate_folder": "family",
            "candidate_subfolder": "siblings",
            "candidate_tags": ["younger-brother"],
            "severity": 0.3,
            "confidence": 0.95,
            "quotes": [{
                "message_id": msg_ids[0],
                "text": "у меня есть младший братишка егор",
            }],
        },
        {
            "summary": "Папа злоупотребляет алкоголем",
            "candidate_folder": "family",
            "candidate_subfolder": "parents",
            "candidate_tags": ["dad-alcohol"],
            "severity": 0.85,
            "confidence": 0.9,
            "quotes": [{
                "message_id": msg_ids[1],
                "text": "папа опять напился вчера",
            }],
        },
        {
            "summary": "Ритуал общения с Кайросом каждый день в 20:00",
            "candidate_folder": "routines",
            "candidate_subfolder": "rituals",
            "candidate_tags": ["daily-checkin", "8pm"],
            "severity": 0.2,
            "confidence": 0.95,
            "quotes": [{
                "message_id": msg_ids[2],
                "text": "я общаюсь с тобой каждый день в 20:00",
            }],
        },
    ], ensure_ascii=False)


async def test_first_run_creates_three_facts(db_with_messages):
    """Первый прогон: создаются 3 факта, чекпойнт сдвигается."""
    user_id = db_with_messages["user_id"]
    msg_ids = db_with_messages["msg_ids"]

    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm(
            _extract_response_for_three_messages(msg_ids),
        )),
    ):
        async with async_session_factory() as db:
            agent = ReflectionAgent(db=db)
            result = await agent.run_for_user(user_id)

    assert result.facts_created == 3
    assert result.facts_updated == 0

    async with async_session_factory() as db:
        from sqlalchemy import select
        facts = (await db.execute(
            select(DossierFact).where(DossierFact.user_id == user_id),
        )).scalars().all()
        assert len(facts) == 3
        # Проверим папки
        folders = {(f.folder, f.subfolder) for f in facts}
        assert ("family", "siblings") in folders
        assert ("family", "parents") in folders
        assert ("routines", "rituals") in folders

        # Чекпойнт указывает на последнее сообщение
        cp = await db.get(DossierCheckpoint, user_id)
        assert cp is not None
        assert cp.last_processed_message_id == msg_ids[-1]
        assert cp.facts_extracted_total == 3


async def test_second_run_with_no_new_messages_does_nothing(db_with_messages):
    """Второй прогон: если новых сообщений нет — ноль действий."""
    user_id = db_with_messages["user_id"]
    msg_ids = db_with_messages["msg_ids"]

    # Первый прогон
    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm(
            _extract_response_for_three_messages(msg_ids),
        )),
    ):
        async with async_session_factory() as db:
            await ReflectionAgent(db=db).run_for_user(user_id)

    # Второй прогон без новых сообщений
    async with async_session_factory() as db:
        agent = ReflectionAgent(db=db)
        result = await agent.run_for_user(user_id)

    assert result.facts_created == 0
    assert result.facts_updated == 0
    assert result.skipped_reason == "no_new_messages"


async def test_empty_extract_advances_checkpoint(db_with_messages):
    """Пустой extract тоже должен сдвинуть чекпойнт (чтобы не пересматривать)."""
    user_id = db_with_messages["user_id"]
    msg_ids = db_with_messages["msg_ids"]

    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm("[]")),
    ):
        async with async_session_factory() as db:
            agent = ReflectionAgent(db=db)
            result = await agent.run_for_user(user_id)

    assert result.facts_created == 0
    # Но last_processed_message_id обновился
    assert result.last_processed_message_id == msg_ids[-1]


async def test_auto_split_glued_folder(db_with_messages):
    """LLM иногда склеивает "family/siblings" в candidate_folder.

    Агент должен авто-расщепить на пару (family, siblings) вместо отбрасывания.
    """
    user_id = db_with_messages["user_id"]
    msg_ids = db_with_messages["msg_ids"]

    # Глюк LLM: candidate_folder = "family/siblings", candidate_subfolder = null
    glued_response = json.dumps([
        {
            "summary": "Есть младший брат Егор",
            "candidate_folder": "family/siblings",  # склеено!
            "candidate_subfolder": None,
            "candidate_tags": ["younger-brother"],
            "severity": 0.2,
            "confidence": 0.9,
            "quotes": [{
                "message_id": msg_ids[0],
                "text": "у меня есть младший братишка егор",
            }],
        },
    ], ensure_ascii=False)

    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm(glued_response)),
    ):
        async with async_session_factory() as db:
            agent = ReflectionAgent(db=db)
            result = await agent.run_for_user(user_id)

    # Должно быть создано 1 факт, не пропущено
    assert result.facts_created == 1
    assert result.candidates_skipped == 0

    # И факт должен быть в правильной паре
    async with async_session_factory() as db:
        from sqlalchemy import select
        f = (await db.execute(select(DossierFact))).scalar_one()
        assert f.folder == "family"
        assert f.subfolder == "siblings"


async def test_invalid_folder_skipped(db_with_messages):
    """Кандидат с невалидной папкой пропускается, остальные обрабатываются."""
    user_id = db_with_messages["user_id"]
    msg_ids = db_with_messages["msg_ids"]

    bad_response = json.dumps([
        {
            "summary": "Невалидный факт",
            "candidate_folder": "nonsense_folder",  # не существует
            "candidate_subfolder": None,
            "candidate_tags": [],
            "severity": 0.5,
            "confidence": 0.5,
            "quotes": [{"message_id": msg_ids[0], "text": "x"}],
        },
        {
            "summary": "Валидный факт",
            "candidate_folder": "values",
            "candidate_subfolder": None,
            "candidate_tags": ["honesty"],
            "severity": 0.4,
            "confidence": 0.7,
            "quotes": [{"message_id": msg_ids[1], "text": "y"}],
        },
    ], ensure_ascii=False)

    with patch(
        "app.core.llm.openai_compat.OpenAICompatProvider.generate",
        new=AsyncMock(return_value=_llm(bad_response)),
    ):
        async with async_session_factory() as db:
            agent = ReflectionAgent(db=db)
            result = await agent.run_for_user(user_id)

    # Один пропущен, один создан
    assert result.candidates_total == 2
    assert result.candidates_skipped == 1
    assert result.facts_created == 1
