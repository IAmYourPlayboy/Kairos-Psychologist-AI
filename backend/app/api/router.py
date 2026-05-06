"""Центральный роутер API — подключает все суб-роутеры."""

from fastapi import APIRouter

from app.api.chat import router as chat_router
from app.api.dossier import router as dossier_router
from app.api.feedback import router as feedback_router
from app.api.health import router as health_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(feedback_router)
api_router.include_router(dossier_router)
