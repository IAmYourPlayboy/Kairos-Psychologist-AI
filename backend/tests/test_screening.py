"""Тесты модуля screening.

Покрытие:
- Чистый scoring ASQ и PSS-4 (unit).
- ScreeningService.save_asq / save_pss4 → запись в БД.
- get_active_asq_positive: окно 7 дней, фильтр по типу, anonymity-match.
- mark_offered + was_recently_offered (Redis-флаг).
- API эндпоинты: GET структуры опросников, POST ответы, GET history,
  POST mark-offered, GET should-offer.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import fakeredis.aioredis as fakeredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Отдельная БД для тестов screening — НЕ трогаем dev-БД
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_screening.db"
os.environ["LLM_API_KEY"] = "test-key"

from app.core.screening.asq import score_asq
from app.core.screening.pss4 import score_pss4
from app.core.screening.service import (
    ScreeningService,
    has_active_asq_positive,
)
from app.data.database import (
    async_session_factory,
    create_all_tables,
    drop_all_tables,
)
from app.data.models import ChatSession, ScreeningResult, User


# ============================================================================
# Unit: ASQ scoring
# ============================================================================


class TestASQScoring:
    """Чистая логика score_asq()."""

    def test_all_no_returns_negative(self):
        result = score_asq({1: "no", 2: "no", 3: "no", 4: "no"})
        assert result.interpretation == "negative"
        assert result.score == 0
        assert result.is_positive is False

    def test_one_yes_no_acuity_returns_non_acute_positive(self):
        """Один yes на 1–4 + 5-й = no → non_acute_positive."""
        result = score_asq({1: "yes", 2: "no", 3: "no", 4: "no", 5: "no"})
        assert result.interpretation == "non_acute_positive"
        assert result.score == 1
        assert result.is_positive is True

    def test_one_yes_with_acuity_yes_returns_acute_positive(self):
        """Один yes на 1–4 + 5-й = yes → acute_positive."""
        result = score_asq({1: "yes", 2: "no", 3: "no", 4: "no", 5: "yes"})
        assert result.interpretation == "acute_positive"
        assert result.score == 2
        assert result.is_positive is True

    def test_no_acuity_when_no_core_yes(self):
        """Если на 1–4 все no — 5-й не учитывается, даже если он yes."""
        # Edge case: технически 5-й yes без core_yes → не positive
        result = score_asq(
            {1: "no", 2: "no", 3: "no", 4: "no", 5: "yes"},
        )
        assert result.interpretation == "negative"
        assert result.is_positive is False

    def test_decline_treated_as_no_for_scoring(self):
        """decline на core-вопросах = не yes → negative если все decline/no."""
        result = score_asq(
            {1: "decline", 2: "no", 3: "decline", 4: "no"},
        )
        assert result.interpretation == "negative"

    def test_decline_on_acuity_with_core_yes(self):
        """decline на 5-м при yes на 1-4 → non_acute (decline ≠ yes)."""
        result = score_asq(
            {1: "yes", 2: "no", 3: "no", 4: "no", 5: "decline"},
        )
        assert result.interpretation == "non_acute_positive"

    def test_missing_core_question_raises(self):
        with pytest.raises(ValueError, match="missing answer"):
            score_asq({1: "no", 2: "no", 3: "no"})  # нет 4-го

    def test_unknown_question_id_raises(self):
        with pytest.raises(ValueError, match="unknown question"):
            score_asq({1: "no", 2: "no", 3: "no", 4: "no", 99: "yes"})

    def test_invalid_answer_raises(self):
        with pytest.raises(ValueError, match="invalid answer"):
            score_asq({1: "maybe", 2: "no", 3: "no", 4: "no"})  # type: ignore[dict-item]


# ============================================================================
# Unit: PSS-4 scoring
# ============================================================================


class TestPSS4Scoring:
    """Чистая логика score_pss4()."""

    def test_all_zeros_returns_low(self):
        # Q1=0, Q4=0 (direct), Q2=0, Q3=0 (reverse) → 0+(4-0)+(4-0)+0 = 8
        # Wait, all 0 means user picked "никогда" for everything.
        # Для reverse Q2/Q3 «никогда» = high stress → 4 points.
        # Итого = 0 + 4 + 4 + 0 = 8 = moderate.
        result = score_pss4({1: 0, 2: 0, 3: 0, 4: 0})
        assert result.score == 8
        assert result.interpretation == "moderate"

    def test_all_fours_returns_high(self):
        # Q1=4, Q4=4 (direct), Q2=4, Q3=4 (reverse) → 4+(4-4)+(4-4)+4 = 8
        # «очень часто» по reverse = низкий стресс → 0 points.
        result = score_pss4({1: 4, 2: 4, 3: 4, 4: 4})
        assert result.score == 8
        assert result.interpretation == "moderate"

    def test_minimum_stress_low(self):
        """Минимальный стресс: Q1/Q4=0 (никогда не теряю контроль),
        Q2/Q3=4 (всегда уверен/всё идёт по-моему) → 0+0+0+0 = 0 → low."""
        result = score_pss4({1: 0, 2: 4, 3: 4, 4: 0})
        assert result.score == 0
        assert result.interpretation == "low"

    def test_maximum_stress_high(self):
        """Максимальный стресс: Q1/Q4=4 (всегда теряю контроль),
        Q2/Q3=0 (никогда не уверен) → 4+(4-0)+(4-0)+4 = 16 → high."""
        result = score_pss4({1: 4, 2: 0, 3: 0, 4: 4})
        assert result.score == 16
        assert result.interpretation == "high"

    def test_moderate_threshold(self):
        # 0–5 low, 6–10 moderate, 11–16 high
        # Подбираем 6: например Q1=2, Q4=2, Q2=4, Q3=4 → 2+0+0+2=4 (low)
        # Q1=3, Q4=3, Q2=4, Q3=4 → 3+0+0+3=6 → moderate
        result = score_pss4({1: 3, 2: 4, 3: 4, 4: 3})
        assert result.score == 6
        assert result.interpretation == "moderate"

    def test_high_threshold(self):
        # 11+ → high. Q1=4, Q4=4, Q2=2, Q3=3 → 4+(4-2)+(4-3)+4 = 11 → high
        result = score_pss4({1: 4, 2: 2, 3: 3, 4: 4})
        assert result.score == 11
        assert result.interpretation == "high"

    def test_missing_answer_raises(self):
        with pytest.raises(ValueError, match="missing answer"):
            score_pss4({1: 2, 2: 3, 3: 1})  # нет 4-го

    def test_out_of_range_answer_raises(self):
        with pytest.raises(ValueError, match="must be 0..4"):
            score_pss4({1: 5, 2: 0, 3: 0, 4: 0})

    def test_negative_answer_raises(self):
        with pytest.raises(ValueError, match="must be 0..4"):
            score_pss4({1: -1, 2: 0, 3: 0, 4: 0})

    def test_non_int_answer_raises(self):
        with pytest.raises(ValueError, match="must be int"):
            score_pss4({1: "two", 2: 0, 3: 0, 4: 0})  # type: ignore[dict-item]


# ============================================================================
# Service: фикстура с чистой БД
# ============================================================================


@pytest_asyncio.fixture
async def clean_db():
    """Чистая БД на каждый сервис-тест."""
    await drop_all_tables()
    await create_all_tables()
    yield
    await drop_all_tables()


@pytest_asyncio.fixture
async def fake_redis():
    fake = fakeredis.FakeRedis()
    yield fake
    await fake.aclose()


# ============================================================================
# Service: save_asq / save_pss4
# ============================================================================


class TestServiceSave:
    """save_asq / save_pss4 → ORM-запись в БД."""

    async def test_save_asq_negative(self, clean_db, fake_redis):
        async with async_session_factory() as db:
            session = ChatSession(id=str(uuid4()), guest_id=str(uuid4()))
            db.add(session)
            await db.commit()

            service = ScreeningService(db, fake_redis)
            result, record = await service.save_asq(
                session_id=session.id,
                answers={1: "no", 2: "no", 3: "no", 4: "no"},
            )

            assert result.interpretation == "negative"
            assert record.questionnaire == "asq"
            assert record.interpretation == "negative"
            assert record.score == 0.0
            assert record.session_id == session.id

    async def test_save_asq_acute_positive(self, clean_db, fake_redis):
        async with async_session_factory() as db:
            session = ChatSession(id=str(uuid4()), guest_id=str(uuid4()))
            db.add(session)
            await db.commit()

            service = ScreeningService(db, fake_redis)
            result, record = await service.save_asq(
                session_id=session.id,
                answers={1: "yes", 2: "no", 3: "yes", 4: "no", 5: "yes"},
            )

            assert result.interpretation == "acute_positive"
            assert record.interpretation == "acute_positive"
            assert record.score == 2.0

    async def test_save_pss4_high(self, clean_db, fake_redis):
        async with async_session_factory() as db:
            session = ChatSession(id=str(uuid4()), guest_id=str(uuid4()))
            db.add(session)
            await db.commit()

            service = ScreeningService(db, fake_redis)
            result, record = await service.save_pss4(
                session_id=session.id,
                answers={1: 4, 2: 0, 3: 0, 4: 4},
            )

            assert result.interpretation == "high"
            assert record.interpretation == "high"
            assert record.score == 16.0


# ============================================================================
# Service: get_active_asq_positive
# ============================================================================


class TestActiveASQPositive:
    """get_active_asq_positive: окно 7 дней + anonymity-match."""

    async def test_finds_recent_positive(self, clean_db, fake_redis):
        user_id = str(uuid4())
        async with async_session_factory() as db:
            db.add(User(id=user_id, email="t@e.com"))
            session = ChatSession(id=str(uuid4()), user_id=user_id)
            db.add(session)
            await db.commit()

            service = ScreeningService(db, fake_redis)
            await service.save_asq(
                session_id=session.id,
                answers={1: "yes", 2: "no", 3: "no", 4: "no", 5: "no"},
            )

            found = await service.get_active_asq_positive(
                user_id=user_id, guest_id=None,
            )
            assert found is not None
            assert found.interpretation == "non_acute_positive"

    async def test_does_not_find_negative(self, clean_db, fake_redis):
        user_id = str(uuid4())
        async with async_session_factory() as db:
            db.add(User(id=user_id, email="t@e.com"))
            session = ChatSession(id=str(uuid4()), user_id=user_id)
            db.add(session)
            await db.commit()

            service = ScreeningService(db, fake_redis)
            await service.save_asq(
                session_id=session.id,
                answers={1: "no", 2: "no", 3: "no", 4: "no"},
            )

            found = await service.get_active_asq_positive(
                user_id=user_id, guest_id=None,
            )
            assert found is None

    async def test_does_not_find_old_positive(self, clean_db, fake_redis):
        """Старее 7 дней — не находит."""
        user_id = str(uuid4())
        async with async_session_factory() as db:
            db.add(User(id=user_id, email="t@e.com"))
            session = ChatSession(id=str(uuid4()), user_id=user_id)
            db.add(session)
            await db.commit()

            service = ScreeningService(db, fake_redis)
            _, record = await service.save_asq(
                session_id=session.id,
                answers={1: "yes", 2: "no", 3: "no", 4: "no", 5: "no"},
            )
            # Подменим created_at на 10 дней назад
            old_ts = datetime.now(timezone.utc) - timedelta(days=10)
            record.created_at = old_ts
            await db.commit()

            found = await service.get_active_asq_positive(
                user_id=user_id, guest_id=None,
            )
            assert found is None

    async def test_finds_by_guest_id(self, clean_db, fake_redis):
        guest_id = str(uuid4())
        async with async_session_factory() as db:
            session = ChatSession(id=str(uuid4()), guest_id=guest_id)
            db.add(session)
            await db.commit()

            service = ScreeningService(db, fake_redis)
            await service.save_asq(
                session_id=session.id,
                answers={1: "yes", 2: "no", 3: "no", 4: "no", 5: "yes"},
            )

            found = await service.get_active_asq_positive(
                user_id=None, guest_id=guest_id,
            )
            assert found is not None
            assert found.interpretation == "acute_positive"

    async def test_does_not_match_other_user(self, clean_db, fake_redis):
        """ASQ-positive у user A не должен находиться по user_id=B."""
        user_a = str(uuid4())
        user_b = str(uuid4())
        async with async_session_factory() as db:
            db.add(User(id=user_a, email="a@e.com"))
            db.add(User(id=user_b, email="b@e.com"))
            session_a = ChatSession(id=str(uuid4()), user_id=user_a)
            db.add(session_a)
            await db.commit()

            service = ScreeningService(db, fake_redis)
            await service.save_asq(
                session_id=session_a.id,
                answers={1: "yes", 2: "no", 3: "no", 4: "no", 5: "yes"},
            )

            found = await service.get_active_asq_positive(
                user_id=user_b, guest_id=None,
            )
            assert found is None

    async def test_no_ids_returns_none(self, clean_db, fake_redis):
        async with async_session_factory() as db:
            service = ScreeningService(db, fake_redis)
            found = await service.get_active_asq_positive(
                user_id=None, guest_id=None,
            )
            assert found is None

    async def test_module_helper_works(self, clean_db, fake_redis):
        """has_active_asq_positive() — bool-хелпер для PerceptionPipeline."""
        guest_id = str(uuid4())
        async with async_session_factory() as db:
            session = ChatSession(id=str(uuid4()), guest_id=guest_id)
            db.add(session)
            await db.commit()

            service = ScreeningService(db, fake_redis)
            await service.save_asq(
                session_id=session.id,
                answers={1: "yes", 2: "no", 3: "no", 4: "no", 5: "yes"},
            )

            assert await has_active_asq_positive(
                db, user_id=None, guest_id=guest_id,
            ) is True
            assert await has_active_asq_positive(
                db, user_id=None, guest_id=str(uuid4()),
            ) is False


# ============================================================================
# Service: mark_offered / was_recently_offered
# ============================================================================


class TestFrequencyCap:
    async def test_mark_then_check(self, clean_db, fake_redis):
        async with async_session_factory() as db:
            service = ScreeningService(db, fake_redis)
            ident = str(uuid4())

            # Сначала — не предлагался
            assert await service.was_recently_offered(
                identifier=ident, questionnaire="asq",
            ) is False

            await service.mark_offered(identifier=ident, questionnaire="asq")

            # Теперь предлагался
            assert await service.was_recently_offered(
                identifier=ident, questionnaire="asq",
            ) is True

    async def test_questionnaires_independent(self, clean_db, fake_redis):
        """Метка по asq не влияет на pss4."""
        async with async_session_factory() as db:
            service = ScreeningService(db, fake_redis)
            ident = str(uuid4())
            await service.mark_offered(identifier=ident, questionnaire="asq")

            assert await service.was_recently_offered(
                identifier=ident, questionnaire="asq",
            ) is True
            assert await service.was_recently_offered(
                identifier=ident, questionnaire="pss4",
            ) is False

    async def test_invalid_questionnaire_raises(self, clean_db, fake_redis):
        async with async_session_factory() as db:
            service = ScreeningService(db, fake_redis)
            with pytest.raises(ValueError, match="Unknown questionnaire"):
                await service.mark_offered(
                    identifier="x", questionnaire="invalid",
                )


# ============================================================================
# Service: history
# ============================================================================


class TestHistory:
    async def test_history_desc_order(self, clean_db, fake_redis):
        user_id = str(uuid4())
        async with async_session_factory() as db:
            db.add(User(id=user_id, email="t@e.com"))
            session = ChatSession(id=str(uuid4()), user_id=user_id)
            db.add(session)
            await db.commit()

            service = ScreeningService(db, fake_redis)
            await service.save_asq(
                session_id=session.id,
                answers={1: "no", 2: "no", 3: "no", 4: "no"},
            )
            await service.save_pss4(
                session_id=session.id,
                answers={1: 0, 2: 4, 3: 4, 4: 0},
            )

            history = await service.get_history(
                user_id=user_id, guest_id=None,
            )
            assert len(history) == 2
            # PSS-4 был сохранён позже → должен быть первым
            assert history[0].questionnaire == "pss4"
            assert history[1].questionnaire == "asq"

    async def test_history_filtered_by_questionnaire(self, clean_db, fake_redis):
        user_id = str(uuid4())
        async with async_session_factory() as db:
            db.add(User(id=user_id, email="t@e.com"))
            session = ChatSession(id=str(uuid4()), user_id=user_id)
            db.add(session)
            await db.commit()

            service = ScreeningService(db, fake_redis)
            await service.save_asq(
                session_id=session.id,
                answers={1: "no", 2: "no", 3: "no", 4: "no"},
            )
            await service.save_pss4(
                session_id=session.id,
                answers={1: 0, 2: 4, 3: 4, 4: 0},
            )

            asq_only = await service.get_history(
                user_id=user_id, guest_id=None, questionnaire="asq",
            )
            assert len(asq_only) == 1
            assert asq_only[0].questionnaire == "asq"


# ============================================================================
# API: эндпоинты
# ============================================================================


@pytest_asyncio.fixture
async def client(monkeypatch) -> AsyncIterator[AsyncClient]:
    """HTTP-клиент с подменой Redis на fakeredis."""
    await drop_all_tables()
    await create_all_tables()
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(
        "app.core.perception.redis_client.get_redis",
        lambda: fake,
    )
    # Также патчим импортированный alias в screening API
    monkeypatch.setattr(
        "app.api.screening.get_redis",
        lambda: fake,
    )
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await fake.aclose()
    await drop_all_tables()


class TestAPIQuestionnaireStructure:
    async def test_get_asq_structure(self, client: AsyncClient):
        resp = await client.get("/api/screening/asq")
        assert resp.status_code == 200
        data = resp.json()
        assert data["questionnaire"] == "asq"
        assert len(data["questions"]) == 5
        # Первые 4 — основные, 5-й — acuity
        assert data["questions"][0]["is_acuity"] is False
        assert data["questions"][4]["is_acuity"] is True
        # Проверяем русский текст
        assert "не быть живым" in data["questions"][0]["text"]
        assert data["answer_options"] == ["yes", "no", "decline"]

    async def test_get_pss4_structure(self, client: AsyncClient):
        resp = await client.get("/api/screening/pss4")
        assert resp.status_code == 200
        data = resp.json()
        assert data["questionnaire"] == "pss4"
        assert len(data["questions"]) == 4
        # Q2, Q3 — reverse
        assert data["questions"][0]["reverse"] is False
        assert data["questions"][1]["reverse"] is True
        assert data["questions"][2]["reverse"] is True
        assert data["questions"][3]["reverse"] is False
        # Шкала
        assert "0" in data["scale"] or 0 in data["scale"]


class TestAPISubmit:
    async def test_post_asq_negative(self, client: AsyncClient):
        # Создаём сессию заранее
        session_id = str(uuid4())
        async with async_session_factory() as db:
            db.add(ChatSession(id=session_id, guest_id=str(uuid4())))
            await db.commit()

        resp = await client.post(
            "/api/screening/asq",
            json={
                "session_id": session_id,
                "answers": {"1": "no", "2": "no", "3": "no", "4": "no"},
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["interpretation"] == "negative"
        assert data["is_positive"] is False
        assert data["score"] == 0
        assert data["record_id"]

    async def test_post_asq_acute_positive(self, client: AsyncClient):
        session_id = str(uuid4())
        async with async_session_factory() as db:
            db.add(ChatSession(id=session_id, guest_id=str(uuid4())))
            await db.commit()

        resp = await client.post(
            "/api/screening/asq",
            json={
                "session_id": session_id,
                "answers": {
                    "1": "yes", "2": "no", "3": "no", "4": "no", "5": "yes",
                },
            },
        )
        assert resp.status_code == 200
        assert resp.json()["interpretation"] == "acute_positive"
        assert resp.json()["is_positive"] is True

    async def test_post_pss4_high(self, client: AsyncClient):
        session_id = str(uuid4())
        async with async_session_factory() as db:
            db.add(ChatSession(id=session_id, guest_id=str(uuid4())))
            await db.commit()

        resp = await client.post(
            "/api/screening/pss4",
            json={
                "session_id": session_id,
                "answers": {"1": 4, "2": 0, "3": 0, "4": 4},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["interpretation"] == "high"
        assert data["score"] == 16

    async def test_post_invalid_session_returns_404(self, client: AsyncClient):
        resp = await client.post(
            "/api/screening/asq",
            json={
                "session_id": str(uuid4()),  # сессия не создана
                "answers": {"1": "no", "2": "no", "3": "no", "4": "no"},
            },
        )
        assert resp.status_code == 404

    async def test_post_invalid_pss4_answer(self, client: AsyncClient):
        session_id = str(uuid4())
        async with async_session_factory() as db:
            db.add(ChatSession(id=session_id, guest_id=str(uuid4())))
            await db.commit()

        resp = await client.post(
            "/api/screening/pss4",
            json={
                "session_id": session_id,
                "answers": {"1": 99, "2": 0, "3": 0, "4": 0},
            },
        )
        assert resp.status_code == 422


class TestAPIHistory:
    async def test_history_via_session_id(self, client: AsyncClient):
        guest_id = str(uuid4())
        session_id = str(uuid4())
        async with async_session_factory() as db:
            db.add(ChatSession(id=session_id, guest_id=guest_id))
            await db.commit()

        # Положим запись через POST
        await client.post(
            "/api/screening/asq",
            json={
                "session_id": session_id,
                "answers": {"1": "no", "2": "no", "3": "no", "4": "no"},
            },
        )

        # Запрашиваем историю
        resp = await client.get(
            f"/api/screening/history?session_id={session_id}",
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["questionnaire"] == "asq"

    async def test_history_no_id_returns_empty(self, client: AsyncClient):
        resp = await client.get("/api/screening/history")
        assert resp.status_code == 200
        assert resp.json()["items"] == []


class TestAPIFrequencyCap:
    async def test_mark_then_should_offer(self, client: AsyncClient):
        ident = str(uuid4())

        # Сначала — should_offer = True
        r1 = await client.get(
            f"/api/screening/should-offer?identifier={ident}&questionnaire=asq",
        )
        assert r1.status_code == 200
        assert r1.json()["should_offer"] is True

        # Помечаем
        r2 = await client.post(
            "/api/screening/mark-offered",
            json={"identifier": ident, "questionnaire": "asq"},
        )
        assert r2.status_code == 200

        # Теперь — should_offer = False
        r3 = await client.get(
            f"/api/screening/should-offer?identifier={ident}&questionnaire=asq",
        )
        assert r3.json()["should_offer"] is False
