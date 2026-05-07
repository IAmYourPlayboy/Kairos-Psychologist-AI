"""Тесты экспорта датасета (Блок B2, Сессия 22).

Покрытие:
- bucket_duration — корректная категоризация
- apply_k_anonymity — отсев уникальных QI-комбинаций
- load_sessions — загрузка из БД с фильтрами
- write_jsonl — корректный JSONL-формат
- export_dataset — полный цикл
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pytest_asyncio

# Отдельная БД для этих тестов — не трогаем dev и других тестов.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./kairos_test_research_export.db"

from app.data.database import (
    async_session_factory,
    create_all_tables,
    drop_all_tables,
)
from app.data.models import ChatSession, FeedbackEvent, Message
from app.data.research_export import (
    ExportedSession,
    apply_k_anonymity,
    bucket_duration,
    export_dataset,
    load_sessions,
    write_jsonl,
)


# ============================================================================
# Bucket duration
# ============================================================================


class TestBucketDuration:
    def test_none(self) -> None:
        assert bucket_duration(None) == "unknown"

    def test_short(self) -> None:
        assert bucket_duration(60) == "<2min"

    def test_medium(self) -> None:
        assert bucket_duration(300) == "2-10min"

    def test_long(self) -> None:
        assert bucket_duration(1200) == "10-30min"

    def test_very_long(self) -> None:
        assert bucket_duration(3600) == ">30min"


# ============================================================================
# K-anonymity
# ============================================================================


def _make_exported(
    sid: str = "s1",
    crisis: str = "normal",
    outcome: str | None = "improved",
    duration: int | None = 300,
) -> ExportedSession:
    return ExportedSession(
        session_id=sid,
        duration_seconds=duration,
        message_count=4,
        crisis_level_max=crisis,
        outcome=outcome,
        self_report_before=None,
        self_report_after=None,
    )


class TestKAnonymity:
    def test_drops_unique_combination(self) -> None:
        # 5 одинаковых + 1 уникальный → последний должен отвалиться
        sessions = [
            _make_exported(f"common-{i}", "normal", "improved", 300)
            for i in range(5)
        ] + [_make_exported("unique", "immediate", "escalated", 60)]

        kept, report = apply_k_anonymity(sessions, k=5)
        assert len(kept) == 5
        assert report.dropped_count == 1
        assert all(s.session_id.startswith("common") for s in kept)

    def test_keeps_all_when_k_satisfied(self) -> None:
        sessions = [
            _make_exported(f"s-{i}", "normal", "improved", 300)
            for i in range(10)
        ]
        kept, report = apply_k_anonymity(sessions, k=5)
        assert len(kept) == 10
        assert report.dropped_count == 0

    def test_drops_all_when_below_k(self) -> None:
        # 4 уникальных сессии при k=5 — все отваливаются
        sessions = [
            _make_exported("a", "immediate", "escalated", 60),
            _make_exported("b", "high", "improved", 600),
            _make_exported("c", "elevated", "no_change", 1200),
            _make_exported("d", "normal", "left", 30),
        ]
        kept, report = apply_k_anonymity(sessions, k=5)
        assert len(kept) == 0
        assert report.dropped_count == 4

    def test_report_has_metadata(self) -> None:
        sessions = [_make_exported(f"s-{i}") for i in range(5)]
        kept, report = apply_k_anonymity(sessions, k=5)
        d = report.to_dict()
        assert d["k"] == 5
        assert d["total_in"] == 5
        assert d["total_out"] == 5

    def test_quasi_identifier_format(self) -> None:
        s = _make_exported(crisis="normal", outcome="improved", duration=300)
        qi = s.quasi_identifier()
        assert qi == ("normal", "improved", "2-10min")

    def test_qi_with_none_outcome(self) -> None:
        s = _make_exported(outcome=None)
        qi = s.quasi_identifier()
        assert qi[1] == "none"


# ============================================================================
# write_jsonl
# ============================================================================


class TestWriteJSONL:
    def test_writes_one_line_per_session(self, tmp_path: Path) -> None:
        sessions = [_make_exported(f"s-{i}") for i in range(3)]
        output = tmp_path / "out.jsonl"
        count = write_jsonl(sessions, output)
        assert count == 3
        lines = output.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3
        # Каждая строка — валидный JSON
        for line in lines:
            obj = json.loads(line)
            assert "session_id" in obj

    def test_empty_list_creates_empty_file(self, tmp_path: Path) -> None:
        output = tmp_path / "empty.jsonl"
        count = write_jsonl([], output)
        assert count == 0
        assert output.exists()
        assert output.read_text() == ""

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        output = tmp_path / "deep" / "nested" / "out.jsonl"
        sessions = [_make_exported()]
        count = write_jsonl(sessions, output)
        assert count == 1
        assert output.exists()


# ============================================================================
# load_sessions (с реальной БД)
# ============================================================================


@pytest_asyncio.fixture
async def fresh_db() -> AsyncIterator[None]:
    """Свежая БД для каждого теста."""
    await drop_all_tables()
    await create_all_tables()
    yield
    await drop_all_tables()


async def _insert_session(
    *,
    sid: str,
    created_at: datetime | None = None,
    crisis: str = "normal",
    outcome: str | None = "improved",
    duration: int | None = 300,
    messages: list[tuple[str, str]] | None = None,  # [(role, content), ...]
    feedback_events: list[str] | None = None,       # ["thumbs_up", ...]
) -> None:
    """Хелпер для вставки тестовой сессии."""
    async with async_session_factory() as db:
        session = ChatSession(
            id=sid,
            created_at=created_at or datetime.now(timezone.utc),
            crisis_level_max=crisis,
            outcome=outcome,
            duration_seconds=duration,
            message_count=len(messages or []),
        )
        db.add(session)
        await db.flush()

        if messages:
            from uuid import uuid4
            for i, (role, content) in enumerate(messages):
                msg = Message(
                    id=str(uuid4()),
                    session_id=sid,
                    role=role,
                    content=content,
                    created_at=datetime.now(timezone.utc) + timedelta(seconds=i),
                    server_timestamp=datetime.now(timezone.utc) + timedelta(seconds=i),
                )
                db.add(msg)

        if feedback_events:
            from uuid import uuid4
            for ev in feedback_events:
                fb = FeedbackEvent(
                    id=str(uuid4()),
                    session_id=sid,
                    event_type=ev,
                )
                db.add(fb)

        await db.commit()


class TestLoadSessions:
    @pytest.mark.asyncio
    async def test_loads_all_sessions(self, fresh_db: None) -> None:
        await _insert_session(sid="s1", messages=[("user", "привет"), ("assistant", "здравствуй")])
        await _insert_session(sid="s2", messages=[("user", "пока")])

        async with async_session_factory() as db:
            sessions = await load_sessions(db)

        assert len(sessions) == 2
        ids = {s.session_id for s in sessions}
        assert ids == {"s1", "s2"}

    @pytest.mark.asyncio
    async def test_filter_by_since(self, fresh_db: None) -> None:
        old_date = datetime.now(timezone.utc) - timedelta(days=30)
        new_date = datetime.now(timezone.utc) - timedelta(days=1)

        await _insert_session(sid="old", created_at=old_date)
        await _insert_session(sid="new", created_at=new_date)

        async with async_session_factory() as db:
            sessions = await load_sessions(
                db, since=datetime.now(timezone.utc) - timedelta(days=7)
            )

        assert len(sessions) == 1
        assert sessions[0].session_id == "new"

    @pytest.mark.asyncio
    async def test_only_with_feedback(self, fresh_db: None) -> None:
        await _insert_session(sid="with_fb", feedback_events=["thumbs_up"])
        await _insert_session(sid="no_fb")

        async with async_session_factory() as db:
            sessions = await load_sessions(db, only_with_feedback=True)

        assert len(sessions) == 1
        assert sessions[0].session_id == "with_fb"

    @pytest.mark.asyncio
    async def test_messages_in_order(self, fresh_db: None) -> None:
        await _insert_session(
            sid="ordered",
            messages=[
                ("user", "первое"),
                ("assistant", "второе"),
                ("user", "третье"),
            ],
        )

        async with async_session_factory() as db:
            sessions = await load_sessions(db)

        assert len(sessions) == 1
        msgs = sessions[0].messages
        assert len(msgs) == 3
        assert msgs[0]["content"] == "первое"
        assert msgs[1]["content"] == "второе"
        assert msgs[2]["content"] == "третье"


# ============================================================================
# export_dataset (E2E)
# ============================================================================


class TestExportDataset:
    @pytest.mark.asyncio
    async def test_full_cycle_writes_jsonl(
        self, fresh_db: None, tmp_path: Path
    ) -> None:
        # 5 одинаковых сессий чтобы пройти k=5
        for i in range(5):
            await _insert_session(
                sid=f"s-{i}",
                messages=[("user", f"сообщение {i}")],
                crisis="normal",
                outcome="improved",
                duration=300,
            )

        output = tmp_path / "export.jsonl"
        result = await export_dataset(output=output, k=5)

        assert result["written"] == 5
        assert result["k_anonymity"]["total_in"] == 5
        assert result["k_anonymity"]["total_out"] == 5
        assert result["k_anonymity"]["dropped_count"] == 0
        assert output.exists()

        # Проверяем формат
        lines = output.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 5
        first = json.loads(lines[0])
        assert "session_id" in first
        assert "messages" in first
        assert first["crisis_level_max"] == "normal"

    @pytest.mark.asyncio
    async def test_filters_unique_via_k(
        self, fresh_db: None, tmp_path: Path
    ) -> None:
        # 5 одинаковых + 1 уникальный
        for i in range(5):
            await _insert_session(
                sid=f"common-{i}",
                crisis="normal",
                outcome="improved",
                duration=300,
            )
        await _insert_session(
            sid="unique",
            crisis="immediate",
            outcome="escalated",
            duration=60,
        )

        output = tmp_path / "export.jsonl"
        result = await export_dataset(output=output, k=5)

        assert result["written"] == 5
        assert result["k_anonymity"]["dropped_count"] == 1
