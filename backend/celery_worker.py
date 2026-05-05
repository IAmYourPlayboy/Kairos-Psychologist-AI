"""Точка входа для Celery worker.

Запуск (из backend/):
    venv\\Scripts\\activate
    celery -A celery_worker:celery_app worker -l info -Q reflection -c 1

На Windows может понадобиться флаг -P solo (если eventlet/gevent не стоят):
    celery -A celery_worker:celery_app worker -l info -Q reflection -c 1 -P solo
"""

from app.celery_app import celery_app

# Импорт задач, чтобы они зарегистрировались в celery_app
from app.core.perception import reflection_tasks  # noqa: F401
