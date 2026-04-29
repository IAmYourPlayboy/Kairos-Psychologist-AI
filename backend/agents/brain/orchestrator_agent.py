"""Агент 5: Orchestrator Agent — главный регулировщик.

Координирует работу всех агентов.
Решает: создать новый модуль, обновить существующий, или запросить больше данных.
"""

import logging
from enum import Enum
from typing import Optional
from datetime import datetime

from agents.shared.base_agent import BaseAgent
from agents.shared.knowledge_base import KnowledgeBase
from agents.brain.validation_agent import ValidationResult
from agents.brain.aggregator_agent import ConsolidatedArticle

logger = logging.getLogger(__name__)


class Decision(Enum):
    """Решения Orchestrator."""
    CREATE_MODULE = "create_module"
    UPDATE_MODULE = "update_module"
    AGGREGATE = "aggregate"  # Нужна новая эталонная статья
    REQUEST_MORE_DATA = "request_more_data"
    SKIP = "skip"  # Недостаточно данных


class OrchestratorAgent(BaseAgent):
    """Главный регулировщик агентов.

    Анализирует результаты валидации и решает, что делать дальше.
    """

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        """Инициализация.

        Args:
            knowledge_base: База знаний для проверки существующих статей
        """
        super().__init__(name="OrchestratorAgent", priority=5)
        self._kb = knowledge_base

    async def run(self, context: dict) -> dict:
        """Принять решение по результатам валидации.

        Args:
            context: {
                "validation_results": list[ValidationResult],
                "topic": str,
                "existing_articles": list[ConsolidatedArticle] — опционально
            }

        Returns:
            {
                "decision": Decision,
                "reasoning": str,
                "action_plan": list[str],
                "next_agent": str
            }
        """
        validation_results = context.get("validation_results", [])
        topic = context.get("topic", "unknown")
        existing = context.get("existing_articles", [])

        logger.info(
            f"Оркестрация для темы '{topic}': "
            f"{len(validation_results)} статей проверено"
        )

        # Подсчёт статистики
        stats = self._calculate_stats(validation_results)

        # Анализ решения
        decision, reasoning = self._make_decision(stats, len(existing), topic)

        # План действий
        action_plan = self._create_action_plan(decision, stats, topic)

        # Кто следующий?
        next_agent = self._get_next_agent(decision)

        logger.info(f"Решение: {decision.value} — {reasoning}")

        return {
            "decision": decision,
            "reasoning": reasoning,
            "action_plan": action_plan,
            "next_agent": next_agent,
            "stats": stats,
        }

    def _calculate_stats(self, results: list) -> dict:
        """Подсчитать статистику по валидации."""
        total = len(results)
        if total == 0:
            return {"total": 0, "high": 0, "medium": 0, "low": 0}

        high = sum(1 for r in results if r.trust_level.value == "HIGH")
        medium = sum(1 for r in results if r.trust_level.value == "MEDIUM")
        low = sum(1 for r in results if r.trust_level.value == "LOW")

        avg_echelon2 = sum(r.echelon_2_score for r in results) / total
        avg_echelon3 = sum(r.echelon_3_consensus for r in results) / total

        return {
            "total": total,
            "high": high,
            "medium": medium,
            "low": low,
            "avg_echelon2": avg_echelon2,
            "avg_echelon3": avg_echelon3,
            "pass_rate": (high + medium) / total if total > 0 else 0,
        }

    def _make_decision(
        self, stats: dict, existing_count: int, topic: str
    ) -> tuple[Decision, str]:
        """Принять решение.

        Rules:
        - Если >5 статей HIGH → создать модуль
        - Если >3 статей + существующая статья → обновить
        - Если <5 статей → запросить больше данных
        - Если <2 статей HIGH → пропустить тему
        """
        if stats["total"] < 3:
            return Decision.SKIP, "Слишком мало статей для анализа"

        if stats["high"] < 2:
            return Decision.SKIP, "Недостаточно качественных источников"

        if stats["high"] >= 5:
            if existing_count > 0:
                return (
                    Decision.UPDATE_MODULE,
                    f"5+ качественных статей + существующая статья → обновить модуль"
                )
            else:
                return (
                    Decision.CREATE_MODULE,
                    f"{stats['high']} качественных статей → создать новый модуль"
                )

        if stats["high"] >= 3:
            if existing_count > 0:
                return (
                    Decision.UPDATE_MODULE,
                    f"{stats['high']} качественных статей → обновить эталонную статью"
                )
            else:
                return (
                    Decision.AGGREGATE,
                    f"{stats['high']} статей → создать эталонную статью"
                )

        if stats["avg_echelon2"] >= 0.6:
            return (
                Decision.REQUEST_MORE_DATA,
                f"Среднее качество ({stats['avg_echelon2']:.2f}), нужно больше данных"
            )

        return Decision.SKIP, "Недостаточно качественных статей"

    def _create_action_plan(
        self, decision: Decision, stats: dict, topic: str
    ) -> list[str]:
        """Создать план действий."""
        plan = []

        if decision == Decision.CREATE_MODULE:
            plan.extend([
                "1. AggregatorAgent → создать эталонную статью",
                "2. IntegratorAgent → встроить в базу",
                "3. ModuleBuilderAgent → создать скилл и модуль",
                "4. Обновить therapy_router.py",
                "5. Добавить в prompts/builder.py",
            ])

        elif decision == Decision.UPDATE_MODULE:
            plan.extend([
                "1. AggregatorAgent → обновить эталонную статью",
                "2. IntegratorAgent → перепроверить конфликты",
                "3. ModuleBuilderAgent → обновить модуль",
            ])

        elif decision == Decision.AGGREGATE:
            plan.extend([
                "1. AggregatorAgent → создать эталонную статью",
                "2. Сохранить в базу знаний",
                "3. Ждать больше данных для модуля",
            ])

        elif decision == Decision.REQUEST_MORE_DATA:
            plan.extend([
                "1. ResearcherAgent → расширить поиск по теме",
                f"2. Искать дополнительные источники по '{topic}'",
            ])

        else:  # SKIP
            plan.append(f"Пропустить тему '{topic}' — недостаточно данных")

        return plan

    def _get_next_agent(self, decision: Decision) -> str:
        """Определить следующего агента."""
        mapping = {
            Decision.CREATE_MODULE: "AggregatorAgent",
            Decision.UPDATE_MODULE: "AggregatorAgent",
            Decision.AGGREGATE: "AggregatorAgent",
            Decision.REQUEST_MORE_DATA: "ResearcherAgent",
            Decision.SKIP: None,
        }
        return mapping.get(decision)