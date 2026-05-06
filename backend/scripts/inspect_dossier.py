"""Утилита: показать всё досье из БД в читабельном виде.

Запуск (из backend/, с активированным venv):
    python scripts/inspect_dossier.py
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.data.database import async_session_factory
from app.data.dossier_models import DossierCheckpoint, DossierFact


async def main() -> None:
    async with async_session_factory() as db:
        # === Факты ===
        stmt = (
            select(DossierFact)
            .options(selectinload(DossierFact.quotes))
            .order_by(DossierFact.user_id, DossierFact.folder, DossierFact.last_mentioned.desc())
        )
        facts = (await db.execute(stmt)).scalars().all()

        if not facts:
            _print("Досье пусто. Ни одного факта не извлечено.")
        else:
            _print(f"=== ФАКТЫ ({len(facts)}) ===")
            current_user = None
            for f in facts:
                if f.user_id != current_user:
                    current_user = f.user_id
                    _print(f"\n--- Пользователь {f.user_id[:8]} ---")
                loc = f"{f.folder}/{f.subfolder}" if f.subfolder else f.folder
                superseded = " [SUPERSEDED]" if f.superseded_by else ""
                _print(
                    f"  [{loc}] sev={f.severity:.2f} conf={f.confidence:.2f} "
                    f"x{f.times_mentioned}{superseded}"
                )
                _print(f"    summary: {f.summary}")
                if f.tags:
                    _print(f"    tags:    {', '.join(f.tags)}")
                for q in f.quotes[:3]:
                    _print(f"    quote:   «{q.text}»")

        # === Чекпойнты ===
        cps = (await db.execute(select(DossierCheckpoint))).scalars().all()
        _print("")
        if not cps:
            _print("Чекпойнтов нет (рефлексия не запускалась).")
        else:
            _print(f"=== ЧЕКПОЙНТЫ ({len(cps)}) ===")
            for cp in cps:
                last_id = (
                    cp.last_processed_message_id[:8]
                    if cp.last_processed_message_id
                    else "—"
                )
                last_at = (
                    cp.last_processed_at.strftime("%Y-%m-%d %H:%M:%S")
                    if cp.last_processed_at
                    else "—"
                )
                _print(
                    f"  user={cp.user_id[:8]} "
                    f"last_msg={last_id} at={last_at} "
                    f"facts_total={cp.facts_extracted_total}"
                )


def _print(s: str) -> None:
    """Печать с UTF-8 в обход cp1252 в Windows-консоли."""
    sys.stdout.buffer.write((s + "\n").encode("utf-8"))


if __name__ == "__main__":
    asyncio.run(main())
