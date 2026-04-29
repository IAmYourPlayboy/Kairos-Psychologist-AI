"""Эндпоинт проверки здоровья сервиса."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Проверка что сервис жив и отвечает."""
    return {
        "status": "ok",
        "app": "Kairos",
        "version": "0.1.0",
    }
