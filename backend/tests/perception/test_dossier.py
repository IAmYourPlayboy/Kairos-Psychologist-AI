"""Тесты DossierService — высокоуровневый CRUD над фактами/цитатами."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
import pytest_asyncio

# Используем отдельный файл SQLite для тестов
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_dossier.db"
os.environ["LLM_API_KEY"] = "test-key"

from app.core.perception.dossier import DossierService
from app.data.database import (
    async_session_factory,
    create_all_tables,
    drop_all_tables,
)
from app.data.models import ChatSession, Message, User


@pytest_asyncio.fixture
async def db_with_user():
    """Создаёт чистую БД с одним пользователем, сессией и одним сообщением."""
    await drop_all_tables()
    await create_all_tables()

    async with async_session_factory() as db:
        user = User(id=str(uuid4()), email="test@example.com")
        db.add(user)
        session = ChatSession(id=str(uuid4()), user_id=user.id)
        db.add(session)
        msg = Message(
            id=str(uuid4()),
            session_id=session.id,
            role="user",
            content="мама ругает за макияж",
        )
        db.add(msg)
        await db.commit()
        yield {
            "user_id": user.id,
            "session_id": session.id,
            "message_id": msg.id,
        }

    await drop_all_tables()


async def test_create_fact(db_with_user):
    """add_fact() создаёт факт с цитатой."""
    async with async_session_factory() as db:
        service = DossierService(db)
        fact = await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="family",
            subfolder="parents",
            summary="Мама критикует внешность",
            tags=["mom-criticism", "appearance-pressure"],
            severity=0.6,
            confidence=0.8,
            quotes=[
                {
                    "text": "мама ругает за макияж",
                    "session_id": db_with_user["session_id"],
                    "message_id": db_with_user["message_id"],
                }
            ],
        )

    assert fact.id
    assert fact.folder == "family"
    assert fact.subfolder == "parents"
    assert fact.times_mentioned == 1
    assert len(fact.tags) == 2
    assert "mom-criticism" in fact.tags


async def test_create_fact_invalid_folder_raises(db_with_user):
    """add_fact() с невалидной папкой → ValueError."""
    async with async_session_factory() as db:
        service = DossierService(db)
        with pytest.raises(ValueError, match="Invalid folder"):
            await service.add_fact(
                user_id=db_with_user["user_id"],
                folder="nonsense",
                subfolder=None,
                summary="x",
                tags=[],
                severity=0.5,
                confidence=0.5,
                quotes=[],
            )


async def test_get_facts_by_folder(db_with_user):
    """get_facts_by_folders() возвращает факты в нужной папке."""
    async with async_session_factory() as db:
        service = DossierService(db)
        await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="family",
            subfolder="parents",
            summary="Мама критикует",
            tags=["mom"],
            severity=0.6,
            confidence=0.8,
            quotes=[],
        )
        await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="health",
            subfolder="appearance",
            summary="Не нравится своё отражение",
            tags=["body-image"],
            severity=0.4,
            confidence=0.7,
            quotes=[],
        )

    async with async_session_factory() as db:
        service = DossierService(db)
        family = await service.get_facts_by_folders(
            db_with_user["user_id"], folders=["family"],
        )
        assert len(family) == 1
        assert family[0].summary == "Мама критикует"


async def test_top_relevant_facts(db_with_user):
    """top_relevant_facts() сортирует по severity * recency * confidence."""
    async with async_session_factory() as db:
        service = DossierService(db)
        # Высокая severity, упомянуто давно
        await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="crisis_history",
            subfolder="past_episodes",
            summary="Кризис 2023",
            tags=[],
            severity=0.95,
            confidence=0.9,
            quotes=[],
        )
        # Низкая severity
        await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="goals",
            subfolder="short_term",
            summary="Сдать экзамен",
            tags=[],
            severity=0.2,
            confidence=0.6,
            quotes=[],
        )

    async with async_session_factory() as db:
        service = DossierService(db)
        top = await service.top_relevant_facts(db_with_user["user_id"], limit=5)
        # Кризис должен быть первым
        assert top[0].summary == "Кризис 2023"


async def test_update_fact_adds_quote(db_with_user):
    """update_fact_with_new_quote() добавляет цитату и счётчик."""
    async with async_session_factory() as db:
        service = DossierService(db)
        fact = await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="family",
            subfolder="parents",
            summary="Мама критикует",
            tags=["mom"],
            severity=0.6,
            confidence=0.8,
            quotes=[
                {
                    "text": "мама ругает",
                    "session_id": db_with_user["session_id"],
                    "message_id": db_with_user["message_id"],
                }
            ],
        )
        fact_id = fact.id

    async with async_session_factory() as db:
        service = DossierService(db)
        updated = await service.update_fact_with_new_quote(
            fact_id=fact_id,
            new_quote={
                "text": "мама опять про мою помаду",
                "session_id": db_with_user["session_id"],
                "message_id": db_with_user["message_id"],
            },
        )

    assert updated.times_mentioned == 2
    assert len(updated.quotes) == 2


async def test_supersede_fact(db_with_user):
    """supersede_fact() помечает старый факт как заменённый."""
    async with async_session_factory() as db:
        service = DossierService(db)
        old = await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="identity", subfolder=None,
            summary="Живёт с мамой",
            tags=[], severity=0.3, confidence=0.7, quotes=[],
        )
        new = await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="identity", subfolder=None,
            summary="Переехал к отцу",
            tags=[], severity=0.5, confidence=0.85, quotes=[],
        )
        await service.supersede_fact(
            old_fact_id=old.id, new_fact_id=new.id,
        )

    async with async_session_factory() as db:
        service = DossierService(db)
        # По умолчанию superseded не возвращается
        active = await service.get_facts_by_folders(
            db_with_user["user_id"],
        )
        assert len(active) == 1
        assert active[0].summary == "Переехал к отцу"
        # Если просим всё — возвращается обе
        all_facts = await service.all_user_facts(db_with_user["user_id"])
        assert len(all_facts) == 2


async def test_delete_fact(db_with_user):
    """delete_fact() удаляет факт пользователя (с каскадом цитат)."""
    async with async_session_factory() as db:
        service = DossierService(db)
        fact = await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="goals", subfolder="short_term",
            summary="x", tags=[], severity=0.3, confidence=0.5, quotes=[],
        )
        fact_id = fact.id

    async with async_session_factory() as db:
        service = DossierService(db)
        await service.delete_fact(
            user_id=db_with_user["user_id"], fact_id=fact_id,
        )

    async with async_session_factory() as db:
        service = DossierService(db)
        facts = await service.all_user_facts(db_with_user["user_id"])
        assert len(facts) == 0


async def test_delete_other_user_fact_raises(db_with_user):
    """delete_fact() с чужим user_id → ValueError."""
    async with async_session_factory() as db:
        service = DossierService(db)
        fact = await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="goals", subfolder="short_term",
            summary="x", tags=[], severity=0.3, confidence=0.5, quotes=[],
        )
        fact_id = fact.id

    other_user = str(uuid4())
    async with async_session_factory() as db:
        service = DossierService(db)
        with pytest.raises(ValueError):
            await service.delete_fact(user_id=other_user, fact_id=fact_id)


async def test_delete_all_for_user(db_with_user):
    """delete_all_for_user() сносит все факты + чекпойнт."""
    async with async_session_factory() as db:
        service = DossierService(db)
        await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="family", subfolder="parents",
            summary="A", tags=[], severity=0.5, confidence=0.7, quotes=[],
        )
        await service.add_fact(
            user_id=db_with_user["user_id"],
            folder="goals", subfolder="short_term",
            summary="B", tags=[], severity=0.3, confidence=0.5, quotes=[],
        )
        await service.update_checkpoint(
            user_id=db_with_user["user_id"],
            last_processed_message_id=db_with_user["message_id"],
            facts_extracted=2,
        )

    async with async_session_factory() as db:
        service = DossierService(db)
        count = await service.delete_all_for_user(db_with_user["user_id"])
        assert count == 2

        # Чекпойнт тоже сброшен
        cp = await service.get_checkpoint(db_with_user["user_id"])
        assert cp is None


async def test_checkpoint_create_and_update(db_with_user):
    """get_checkpoint / update_checkpoint работают корректно."""
    async with async_session_factory() as db:
        service = DossierService(db)
        # Сначала чекпойнта нет
        cp = await service.get_checkpoint(db_with_user["user_id"])
        assert cp is None

        # Создаём
        cp = await service.update_checkpoint(
            user_id=db_with_user["user_id"],
            last_processed_message_id=db_with_user["message_id"],
            facts_extracted=3,
        )
        assert cp.last_processed_message_id == db_with_user["message_id"]
        assert cp.facts_extracted_total == 3

    async with async_session_factory() as db:
        service = DossierService(db)
        # Обновляем — facts_extracted_total накапливается
        cp = await service.update_checkpoint(
            user_id=db_with_user["user_id"],
            last_processed_message_id=db_with_user["message_id"],
            facts_extracted=2,
        )
        assert cp.facts_extracted_total == 5  # 3 + 2
