"""Celery-приложение для фоновых задач (ReflectionAgent и др.).

Дизайн: §7 в spec.

Запуск воркера:
    cd backend
    venv\\Scripts\\activate
    celery -A celery_worker:celery_app worker -l info -Q reflection -c 1

(один воркер с concurrency=1 хватает для MVP, потом масштабируем.)
"""

from __future__ import annotations

from celery import Celery

from app.config import settings


celery_app = Celery(
    "kairos",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.core.perception.reflection_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Очереди
    task_default_queue="default",
    task_routes={
        "app.core.perception.reflection_tasks.run_reflection": {
            "queue": "reflection",
        },
    },
    # Поведение задач
    task_acks_late=True,            # ack только после успеха (retry-friendly)
    task_reject_on_worker_lost=True,
    task_track_started=True,
    # Retry дефолты
    task_default_retry_delay=60,
    task_max_retries=3,
    # Result expiration — 24h
    result_expires=24 * 60 * 60,
)
