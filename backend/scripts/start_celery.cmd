@echo off
REM Запуск Celery worker для ReflectionAgent.
REM
REM Использование (из backend/):
REM     scripts\start_celery.cmd
REM
REM Что делает:
REM 1. Активирует venv (если ты его уже активировал — повторно безопасно).
REM 2. Запускает worker с флагами:
REM    -A celery_worker:celery_app — модуль приложения
REM    -l info                     — уровень логов
REM    -Q reflection               — очередь, которую слушать
REM    -c 1                        — concurrency = 1 worker thread
REM    -P solo                     — pool=solo (обязательно на Windows)

call venv\Scripts\activate.bat
celery -A celery_worker:celery_app worker -l info -Q reflection -c 1 -P solo
