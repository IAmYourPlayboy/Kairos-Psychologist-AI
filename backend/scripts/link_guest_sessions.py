"""Утилита: привязать все гостевые ChatSession к первому пользователю.

Используется только во время разработки, до того как появится регистрация
(Блок 13). После регистрации — этот скрипт будет не нужен.

Запуск (из backend/):
    python scripts/link_guest_sessions.py
"""

from __future__ import annotations

import asyncio
import sys
from uuid import uuid4

from sqlalchemy import select, update

from app.data.database import async_session_factory
from app.data.models import ChatSession, User


def _print(s: str) -> None:
    sys.stdout.buffer.write((s + "\n").encode("utf-8"))


async def main() -> None:
    async with async_session_factory() as db:
        user = (
            await db.execute(select(User).limit(1))
        ).scalar_one_or_none()

        if user is None:
            user_id = str(uuid4())
            db.add(User(id=user_id, email="dev-test@kairos.local"))
            await db.flush()
            _print(f"Создан тестовый user: {user_id}")
        else:
            user_id = user.id
            _print(f"Найден существующий user: {user_id}")

        result = await db.execute(
            update(ChatSession)
            .where(ChatSession.user_id.is_(None))
            .values(user_id=user_id)
        )
        await db.commit()
        _print(f"Привязано гостевых сессий: {result.rowcount}")


if __name__ == "__main__":
    asyncio.run(main())
