"""Утилита: сбросить чекпойнт ReflectionAgent для всех пользователей.

После сброса при следующем запуске рефлексии агент перечитает ВСЕ
user-сообщения и попробует извлечь факты заново. Полезно для отладки —
если правил промпт и хочешь проверить на тех же данных.

Запуск (из backend/, с активированным venv):
    python scripts/reset_checkpoint.py
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import delete

from app.data.database import async_session_factory
from app.data.dossier_models import DossierCheckpoint


def _print(s: str) -> None:
    sys.stdout.buffer.write((s + "\n").encode("utf-8"))


async def main() -> None:
    async with async_session_factory() as db:
        result = await db.execute(delete(DossierCheckpoint))
        await db.commit()
        _print(f"Удалено чекпойнтов: {result.rowcount}")
        _print("При следующем запуске reflection — все user-сообщения "
               "будут переобработаны.")


if __name__ == "__main__":
    asyncio.run(main())
