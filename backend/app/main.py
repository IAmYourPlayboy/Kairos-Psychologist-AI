"""Точка входа FastAPI-приложения Kairos."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.core.llm.factory import _reset_provider, get_provider
from app.data.database import dispose_engine
from app.middleware import (
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    register_error_handlers,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Жизненный цикл приложения: startup / shutdown.

    На startup:
        - Настраиваем логирование
        - (LLM-клиент инициализируется лениво при первом запросе)
        - (БД подключается лениво при первом запросе)

    На shutdown:
        - Закрываем HTTP-клиент LLM-провайдера
        - Закрываем пул соединений к БД
    """
    # === Startup ===
    logging.basicConfig(level=settings.log_level.upper())
    logger.info("Kairos запускается (debug=%s, db=%s)",
                settings.debug,
                "sqlite" if settings.is_sqlite else "postgresql")

    yield

    # === Shutdown ===
    # 1. LLM-провайдер
    try:
        await get_provider().close()
    except ValueError:
        pass  # Провайдер не был инициализирован
    _reset_provider()

    # 2. БД
    await dispose_engine()

    logger.info("Kairos завершает работу")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware (порядок: последний добавленный — первый в цепочке).
# При запросе цепочка: SecurityHeaders → RequestID → CORS → endpoint
# При ответе наоборот: endpoint → CORS → RequestID → SecurityHeaders → клиент
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Глобальные обработчики ошибок (HTTP, validation, unhandled)
register_error_handlers(app)

# Роутеры
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
