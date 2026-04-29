"""Центральный роутер API — подключает все суб-роутеры."""

from fastapi import APIRouter

from app.api.health import router as health_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
