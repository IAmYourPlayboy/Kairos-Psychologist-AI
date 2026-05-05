"""Alembic env.py — настройка миграций.

Особенности:
- DATABASE_URL берётся из `app.config.settings` (а не из alembic.ini)
- Поддержка async-движка (через `run_sync` в run_migrations_online)
- Автогенерация миграций из моделей `app.data.models`

Команды (выполнять из папки `backend/`):

    # Создать первую миграцию (после изменения моделей):
    alembic revision --autogenerate -m "initial tables"

    # Применить все миграции:
    alembic upgrade head

    # Откатить последнюю:
    alembic downgrade -1

    # Посмотреть историю:
    alembic history
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Добавляем backend/ в sys.path, чтобы импорты "from app..." работали
import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from app.config import settings  # noqa: E402
from app.data.models import Base  # noqa: E402

# Конфиг Alembic
config = context.config

# Подменяем sqlalchemy.url из settings (а не из alembic.ini)
config.set_main_option("sqlalchemy.url", settings.database_url)

# Логирование
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные моделей — для автогенерации
target_metadata = Base.metadata


# ============================================================================
# Offline-режим (генерация SQL без подключения к БД)
# ============================================================================


def run_migrations_offline() -> None:
    """Запустить миграции в offline-режиме.

    Генерирует SQL-скрипт без реального подключения к БД.
    Полезно для CI/CD или ручной проверки миграций.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Сравнивать типы колонок (для autogenerate)
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================================
# Online-режим (применение миграций к реальной БД)
# ============================================================================


def do_run_migrations(connection: Connection) -> None:
    """Запустить миграции через переданное соединение."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Сравнивать типы колонок
        compare_server_default=True,  # Сравнивать default-значения
        # SQLite: использовать batch_alter_table для ALTER TABLE
        render_as_batch=settings.is_sqlite,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Запустить миграции через async-движок."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Запустить миграции в online-режиме (с подключением к БД)."""
    asyncio.run(run_async_migrations())


# ============================================================================
# Точка входа
# ============================================================================


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
