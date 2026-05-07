"""Тесты финального удаления аккаунта (Celery-таск).

Покрытие:
- Аккаунты с истёкшим deletion_scheduled_at реально удаляются
- Аккаунты с deletion_scheduled_at в будущем НЕ трогаются
- Сессии и сообщения отвязываются (для data flywheel), не удаляются
- Досье удаляется полностью
- Согласия удаляются
- Refresh-токены удаляются
- Идемпотентность: повторный запуск не вредит
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest_asyncio

os.environ["DATABASE_URL"] = (
    "sqlite+aiosqlite:///./kairos_test_account_deletion.db"
)
os.environ["LLM_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-32-chars-min-aaa"

from sqlalchemy import select

from app.core.auth.account_deletion import (
    finalize_pending_deletions,
    schedule_account_deletion,
)
from app.core.auth.password import hash_password
from app.data.database import (
    async_session_factory,
    create_all_tables,
    drop_all_tables,
)
from app.data.dossier_models import (
    DossierCheckpoint,
    DossierFact,
    DossierQuote,
)
from app.data.models import (
    ChatSession,
    Message,
    RefreshToken,
    User,
    UserConsent,
)


@pytest_asyncio.fixture
async def fresh_db() -> AsyncIterator[None]:
    await drop_all_tables()
    await create_all_tables()
    yield
    await drop_all_tables()


async def _create_user_with_data(
    *,
    deletion_scheduled_at: datetime | None,
    email: str = "u@example.com",
) -> str:
    """Создать User с сессией, сообщениями, досье, согласием. Вернуть user_id."""
    user_id = str(uuid4())
    session_id = str(uuid4())
    fact_id = str(uuid4())

    async with async_session_factory() as db:
        user = User(
            id=user_id,
            email=email,
            password_hash=hash_password("anypass123"),
            deletion_scheduled_at=deletion_scheduled_at,
        )
        db.add(user)
        await db.flush()

        # Сессия с сообщениями
        session = ChatSession(
            id=session_id,
            user_id=user_id,
            crisis_level_max="normal",
            message_count=2,
        )
        db.add(session)
        await db.flush()

        db.add(Message(
            id=str(uuid4()),
            session_id=session_id,
            role="user",
            content="привет",
        ))
        db.add(Message(
            id=str(uuid4()),
            session_id=session_id,
            role="assistant",
            content="здравствуй",
        ))

        # Досье
        fact = DossierFact(
            id=fact_id,
            user_id=user_id,
            folder="family",
            subfolder="parents",
            summary="папа",
            tags=[],
            severity=0.5,
            confidence=0.8,
        )
        db.add(fact)
        await db.flush()

        db.add(DossierQuote(
            id=str(uuid4()),
            fact_id=fact_id,
            text="мой папа",
            session_id=session_id,
            message_id=str(uuid4()),
        ))

        db.add(DossierCheckpoint(
            user_id=user_id,
            last_processed_message_id=None,
            last_processed_at=datetime.now(timezone.utc),
            facts_extracted_total=1,
        ))

        # Согласие
        db.add(UserConsent(
            user_id=user_id,
            consent_type="terms_of_service",
            document_version="1.0",
        ))

        # Refresh-токен (уникальный hash на каждого юзера)
        db.add(RefreshToken(
            id=str(uuid4()),
            user_id=user_id,
            token_hash=user_id.replace("-", "")[:64].ljust(64, "a"),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        ))

        await db.commit()

    return user_id


# ============================================================================
# schedule_account_deletion
# ============================================================================


class TestScheduleAccountDeletion:
    async def test_sets_scheduled_at(self, fresh_db: None) -> None:
        user_id = await _create_user_with_data(deletion_scheduled_at=None)
        async with async_session_factory() as db:
            user = await db.get(User, user_id)
            assert user is not None
            await schedule_account_deletion(db, user=user)
            await db.commit()

        async with async_session_factory() as db:
            user = await db.get(User, user_id)
            assert user is not None
            assert user.deletion_scheduled_at is not None
            now = datetime.now(timezone.utc)
            scheduled = user.deletion_scheduled_at
            if scheduled.tzinfo is None:
                scheduled = scheduled.replace(tzinfo=timezone.utc)
            # 7 дней (плюс-минус минута)
            delta = scheduled - now
            assert timedelta(days=6, hours=23) < delta < timedelta(days=7, minutes=1)

    async def test_revokes_all_refresh_tokens(self, fresh_db: None) -> None:
        user_id = await _create_user_with_data(deletion_scheduled_at=None)

        async with async_session_factory() as db:
            user = await db.get(User, user_id)
            assert user is not None
            await schedule_account_deletion(db, user=user)
            await db.commit()

        async with async_session_factory() as db:
            tokens = (await db.execute(
                select(RefreshToken).where(RefreshToken.user_id == user_id),
            )).scalars().all()
            assert all(t.revoked_at is not None for t in tokens)


# ============================================================================
# finalize_pending_deletions
# ============================================================================


class TestFinalizePendingDeletions:
    async def test_no_users_returns_empty_stats(self, fresh_db: None) -> None:
        async with async_session_factory() as db:
            stats = await finalize_pending_deletions(db)
        assert stats["users_deleted"] == 0

    async def test_does_not_delete_future_scheduled(
        self, fresh_db: None,
    ) -> None:
        future = datetime.now(timezone.utc) + timedelta(days=3)
        user_id = await _create_user_with_data(deletion_scheduled_at=future)

        async with async_session_factory() as db:
            stats = await finalize_pending_deletions(db)

        assert stats["users_deleted"] == 0

        async with async_session_factory() as db:
            user = await db.get(User, user_id)
            assert user is not None  # ещё жив

    async def test_deletes_expired(self, fresh_db: None) -> None:
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        user_id = await _create_user_with_data(deletion_scheduled_at=past)

        async with async_session_factory() as db:
            stats = await finalize_pending_deletions(db)

        assert stats["users_deleted"] == 1

        async with async_session_factory() as db:
            assert await db.get(User, user_id) is None

    async def test_sessions_anonymized_not_deleted(
        self, fresh_db: None,
    ) -> None:
        """Сессии и сообщения остаются в БД — для data flywheel."""
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        user_id = await _create_user_with_data(deletion_scheduled_at=past)

        async with async_session_factory() as db:
            await finalize_pending_deletions(db)

        async with async_session_factory() as db:
            # Сессии остались, но user_id обнулён
            sessions = (await db.execute(
                select(ChatSession),
            )).scalars().all()
            assert len(list(sessions)) == 1
            for s in sessions:
                assert s.user_id is None
                assert s.guest_id is None

            # Сообщения остались
            messages = (await db.execute(select(Message))).scalars().all()
            assert len(list(messages)) == 2

    async def test_dossier_deleted(self, fresh_db: None) -> None:
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        user_id = await _create_user_with_data(deletion_scheduled_at=past)

        async with async_session_factory() as db:
            await finalize_pending_deletions(db)

        async with async_session_factory() as db:
            facts = (await db.execute(select(DossierFact))).scalars().all()
            assert len(list(facts)) == 0
            quotes = (await db.execute(select(DossierQuote))).scalars().all()
            assert len(list(quotes)) == 0
            cps = (await db.execute(select(DossierCheckpoint))).scalars().all()
            assert len(list(cps)) == 0

    async def test_consents_deleted(self, fresh_db: None) -> None:
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        await _create_user_with_data(deletion_scheduled_at=past)

        async with async_session_factory() as db:
            await finalize_pending_deletions(db)

        async with async_session_factory() as db:
            consents = (await db.execute(select(UserConsent))).scalars().all()
            assert len(list(consents)) == 0

    async def test_refresh_tokens_deleted(self, fresh_db: None) -> None:
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        await _create_user_with_data(deletion_scheduled_at=past)

        async with async_session_factory() as db:
            await finalize_pending_deletions(db)

        async with async_session_factory() as db:
            tokens = (await db.execute(select(RefreshToken))).scalars().all()
            assert len(list(tokens)) == 0

    async def test_idempotent(self, fresh_db: None) -> None:
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        await _create_user_with_data(deletion_scheduled_at=past)

        async with async_session_factory() as db:
            stats1 = await finalize_pending_deletions(db)

        async with async_session_factory() as db:
            stats2 = await finalize_pending_deletions(db)

        assert stats1["users_deleted"] == 1
        assert stats2["users_deleted"] == 0

    async def test_only_affects_expired_user(
        self, fresh_db: None,
    ) -> None:
        """Если есть и future, и past пользователи — удаляется только past."""
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        future = datetime.now(timezone.utc) + timedelta(days=3)

        past_uid = await _create_user_with_data(
            deletion_scheduled_at=past, email="past@e.com",
        )
        future_uid = await _create_user_with_data(
            deletion_scheduled_at=future, email="future@e.com",
        )
        # Третий пользователь без удаления
        normal_uid = await _create_user_with_data(
            deletion_scheduled_at=None, email="normal@e.com",
        )

        async with async_session_factory() as db:
            stats = await finalize_pending_deletions(db)

        assert stats["users_deleted"] == 1

        async with async_session_factory() as db:
            assert await db.get(User, past_uid) is None
            assert await db.get(User, future_uid) is not None
            assert await db.get(User, normal_uid) is not None
