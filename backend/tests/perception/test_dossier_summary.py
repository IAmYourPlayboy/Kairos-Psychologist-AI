"""Тесты сборки текстовой выжимки досье для промптов."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.perception.dossier_summary import (
    facts_to_compact_summary,
    facts_to_full_dossier_block,
)
from app.data.dossier_models import DossierFact, DossierQuote


def _fact(folder, subfolder, summary, severity=0.5, tags=None) -> DossierFact:
    """Создать DossierFact в памяти (без БД) для теста."""
    f = DossierFact(
        id="fact-1",
        user_id="user-1",
        folder=folder,
        subfolder=subfolder,
        summary=summary,
        tags=tags or [],
        severity=severity,
        confidence=0.8,
        first_mentioned=datetime.now(timezone.utc),
        last_mentioned=datetime.now(timezone.utc),
        times_mentioned=1,
        source_session_ids=[],
        source_message_ids=[],
        superseded_by=None,
    )
    f.quotes = []
    return f


def test_compact_summary_empty_returns_placeholder():
    s = facts_to_compact_summary([])
    assert "пусто" in s.lower()


def test_compact_summary_lists_facts():
    facts = [
        _fact("family", "parents", "Папа пьёт", severity=0.95),
        _fact("relationships", "school_peers", "Травля в школе", severity=0.8),
    ]
    s = facts_to_compact_summary(facts)
    assert "Папа пьёт" in s
    assert "Травля" in s
    assert "family/parents" in s
    assert "relationships/school_peers" in s


def test_compact_summary_includes_severity():
    facts = [_fact("family", "parents", "x", severity=0.95)]
    s = facts_to_compact_summary(facts)
    assert "0.95" in s


def test_full_block_empty_returns_empty_string():
    """Если фактов нет — возвращаем пустую строку (блок не нужен в промпте)."""
    assert facts_to_full_dossier_block([]) == ""


def test_full_block_includes_quotes():
    f = _fact("family", "parents", "Папа пьёт", severity=0.95)
    f.quotes = [
        DossierQuote(
            id="q-1", fact_id=f.id,
            text="вчера папа опять напился",
            session_id="s-1", message_id="m-1",
            created_at=datetime.now(timezone.utc),
        ),
    ]
    block = facts_to_full_dossier_block([f])
    assert "Папа пьёт" in block
    assert "вчера папа опять напился" in block
    assert "ЧТО Я ЗНАЮ" in block


def test_full_block_groups_by_folder():
    f1 = _fact("family", "parents", "A")
    f2 = _fact("family", "siblings", "B")
    block = facts_to_full_dossier_block([f1, f2])
    assert "family/parents" in block
    assert "family/siblings" in block


def test_full_block_limits_quotes_per_fact():
    """В блок попадают последние 3 цитаты, не все."""
    f = _fact("family", "parents", "x")
    f.quotes = [
        DossierQuote(
            id=f"q-{i}", fact_id=f.id,
            text=f"цитата {i}",
            session_id="s", message_id=f"m-{i}",
            created_at=datetime.now(timezone.utc),
        )
        for i in range(5)
    ]
    block = facts_to_full_dossier_block([f])
    # Цитаты 2, 3, 4 (последние 3)
    assert "цитата 2" in block
    assert "цитата 3" in block
    assert "цитата 4" in block
    # Первая цитата не должна попасть
    assert "цитата 0" not in block
