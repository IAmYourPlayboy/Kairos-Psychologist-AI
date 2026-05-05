"""Эндпоинты проверки здоровья сервиса.

- GET /api/health    — базовая проверка (сервис жив)
- GET /api/health/db — проверка подключения к БД
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.data.database import get_db

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Базовая проверка: сервис жив и отвечает."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "0.1.0",
    }


@router.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)) -> dict:
    """Проверка подключения к БД (выполняет SELECT 1)."""
    try:
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        return {
            "status": "ok" if value == 1 else "fail",
            "database": "sqlite" if settings.is_sqlite else "postgresql",
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database unavailable: {type(e).__name__}",
        )
