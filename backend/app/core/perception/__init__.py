"""Слой восприятия Кайроса.

Группа компонентов, превращающих сообщение пользователя в богатый контекст
для основной LLM:

- analyzer.py        — MessageAnalyzer (LLM-вызов, PerceptionReport)
- analyzer_prompt.py — Системный промпт анализатора и сборщик user-prompt
- mood.py            — Mood (6 осей в Redis, формулы обновления)
- dossier.py         — DossierService (CRUD над фактами/цитатами)
- dossier_summary.py — Сериализация фактов в текст для промптов
- folders.py         — Фиксированный список папок и подпапок
- prompt_builder.py  — Сборка промпта для основной LLM
- pipeline.py        — PerceptionPipeline (оркестратор одного цикла)
- redis_client.py    — Singleton Redis-клиент
- types.py           — Pydantic-модели (PerceptionReport, MoodState и т.д.)
- reflection_agent.py — Фоновый агент извлечения фактов (Фаза 5)
- reflection_prompt.py — Промпты для extract / dedupe (Фаза 5)
- reflection_tasks.py  — Celery-таски и scheduling (Фаза 5)

См. полный дизайн: docs/superpowers/specs/2026-05-02-perception-layer-design.md
План: docs/superpowers/plans/2026-05-02-perception-layer-plan.md
"""
