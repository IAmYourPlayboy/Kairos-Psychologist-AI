"""Точка входа FastAPI-приложения Kairos."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.core.llm.factory import _reset_provider, get_provider
from app.middleware.request_id import RequestIDMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Жизненный цикл приложения: startup / shutdown."""
    logging.basicConfig(level=settings.log_level.upper())
    logger.info("Kairos запускается (debug=%s)", settings.debug)
    yield
    # Закрываем HTTP-клиент LLM-провайдера
    try:
        await get_provider().close()
    except ValueError:
        pass  # Провайдер не был инициализирован
    _reset_provider()
    logger.info("Kairos завершает работу")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware (порядок: последний добавленный — первый в цепочке)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)

# Роутеры
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
