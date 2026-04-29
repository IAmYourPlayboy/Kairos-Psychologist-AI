"""Отдел "Мозг Кайроса" — работа с научными статьями.

Пайплайн:
    Researcher → Validation → Orchestrator → Aggregator → Integrator → ModuleBuilder
                                                                ↓
                                                           ReReview (раз в 3-6 месяцев)

См. agents/runner.py для запуска полного пайплайна.
"""
