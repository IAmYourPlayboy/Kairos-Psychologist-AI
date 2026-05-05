"""Подключение к базе данных и зависимости FastAPI.

Использование в эндпоинтах:

    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.data.database import get_db

    @router.post("/chat")
    async def chat(message: str, db: AsyncSession = Depends(get_db)):
        # ... работа с БД через db ...
        await db.commit()

Решения:
- Async-движок (`create_async_engine`) для совместимости с FastAPI.
- `expire_on_commit=False` — иначе после `commit()` объекты становятся недоступны.
- SQLite: `connect_args={"check_same_thread": False}` — обязательно для async.
- `engine.dispose()` вызывается в lifespan приложения при shutdown.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings


# ============================================================================
# Создание движка
# ============================================================================


def _make_engine() -> AsyncEngine:
    """Создать движок на основе настроек.

    Для SQLite добавляем check_same_thread=False (требование async).
    """
    connect_args: dict = {}
    if settings.is_sqlite:
        # SQLite не любит шаренные коннекшены между потоками async-loop'ов
        connect_args["check_same_thread"] = False

    return create_async_engine(
        settings.database_url,
        echo=settings.debug,  # При debug=True логируем все SQL
        connect_args=connect_args,
        pool_pre_ping=True,  # Проверять соединение перед использованием
    )


# Глобальный движок (один на приложение)
engine: AsyncEngine = _make_engine()

# Фабрика сессий
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Объекты остаются доступными после commit()
    autoflush=False,
)


# ============================================================================
# Зависимости FastAPI
# ============================================================================


async def get_db() -> AsyncIterator[AsyncSession]:
    """Зависимость FastAPI: выдаёт сессию БД на время одного запроса.

    Сессия автоматически закрывается после обработки запроса.
    Если внутри произошла ошибка — откат транзакции.

    Используется как `db: AsyncSession = Depends(get_db)`.
    """
    async with async_session_factory() as session:
        try:
            yield session
            # commit() остаётся на совести эндпоинта
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def dispose_engine() -> None:
    """Закрыть пул соединений. Вызывается в lifespan при shutdown."""
    await engine.dispose()


# ============================================================================
# Утилита для тестов / первичной инициализации
# ============================================================================


async def create_all_tables() -> None:
    """Создать все таблицы из моделей (без Alembic).

    Используется только в тестах или при разработке без миграций.
    В продакшене всегда используйте Alembic.
    """
    # Импортируем модели чтобы они зарегистрировались в метаданных
    from app.data import models  # noqa: F401

    from app.data.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    """Удалить все таблицы (только для тестов!)."""
    from app.data import models  # noqa: F401

    from app.data.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
