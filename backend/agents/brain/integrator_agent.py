"""Агент 4: Integrator Agent — встраивание в базу без конфликтов."""

import logging
from typing import Optional

from enum import Enum

from agents.shared.base_agent import BaseAgent
from agents.shared.knowledge_base import KnowledgeBase
from agents.brain.aggregator_agent import ConsolidatedArticle

logger = logging.getLogger(__name__)


class ConflictResolution(Enum):
    """Как разрешать конфликты между источниками."""
    REPLACE = "replace"      # Новое сильнее старого
    KEEP_BOTH = "keep_both"  # Добавить с пометкой
    MERGE = "merge"          # Объединить как альтернативы
    SKIP = "skip"            # Не добавлять


class IntegratorAgent(BaseAgent):
    """Агент интеграции знаний.

    Встраивает эталонные статьи в базу без конфликтов.
    """

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        """Инициализация."""
        super().__init__(name="IntegratorAgent", priority=4)
        self._kb = knowledge_base

    async def run(self, context: dict) -> dict:
        """Интегрировать статью в базу.

        Args:
            context: {
                "article": ConsolidatedArticle,
                "check_conflicts": bool = True
            }

        Returns:
            {
                "status": "integrated" | "conflicts_detected" | "rejected",
                "conflicts": list[dict],
                "resolution": str
            }
        """
        article: ConsolidatedArticle = context["article"]
        check_conflicts = context.get("check_conflicts", True)

        logger.info(f"Интеграция статьи: {article.id}")

        if not check_conflicts:
            # Просто сохранить
            self._kb.save_article(article)
            return {
                "status": "integrated",
                "conflicts": [],
                "resolution": "без проверки конфликтов"
            }

        # Проверить конфликты
        conflicts = await self._detect_conflicts(article)

        if not conflicts:
            # Нет конфликтов — сохранить
            self._kb.save_article(article)
            logger.info(f"Статья {article.id} интегрирована без конфликтов")
            return {
                "status": "integrated",
                "conflicts": [],
                "resolution": "нет конфликтов"
            }

        # Есть конфликты — разрешить
        logger.info(f"Обнаружено {len(conflicts)} конфликтов")
        resolution = await self._resolve_conflicts(article, conflicts)

        return {
            "status": "integrated",
            "conflicts": conflicts,
            "resolution": resolution,
        }

    async def _detect_conflicts(
        self, article: ConsolidatedArticle
    ) -> list[dict]:
        """Найти конфликты с существующими статьями."""
        conflicts = []

        # Найти статьи по той же теме
        existing_articles = self._kb.search_by_tag(article.topic)

        for existing in existing_articles:
            if existing.id == article.id:
                continue

            # Сравнить консенсус
            if self._are_conflicting(article.consensus, existing.consensus):
                conflicts.append({
                    "existing_id": existing.id,
                    "existing_consensus": existing.consensus[:200],
                    "new_consensus": article.consensus[:200],
                    "conflict_type": "contradiction",
                })

        return conflicts

    def _are_conflicting(self, consensus1: str, consensus2: str) -> bool:
        """Определить, противоречат ли два консенсуса.

        Упрощённая проверка на ключевые слова-маркеры.
        """
        # Ключевые слова-маркеры противоречий
        contradiction_markers = [
            ("не помогает", "помогает"),
            ("не эффективен", "эффективен"),
            ("вредно", "полезно"),
            ("нет стадий", "есть стадии"),
            ("линейно", "нелинейно"),
        ]

        c1_lower = consensus1.lower()
        c2_lower = consensus2.lower()

        for marker1, marker2 in contradiction_markers:
            has1 = marker1 in c1_lower or marker2 in c1_lower
            has2 = marker1 in c2_lower or marker2 in c2_lower

            if has1 and has2:
                # Один говорит "да", другой "нет"
                if (marker1 in c1_lower and marker2 in c2_lower) or \
                   (marker2 in c1_lower and marker1 in c2_lower):
                    return True

        return False

    async def _resolve_conflicts(
        self, article: ConsolidatedArticle, conflicts: list
    ) -> str:
        """Разрешить конфликты.

        Returns:
            Стратегия разрешения
        """
        # Стратегия: если новых источников больше — обновить
        # Если источники равны — пометить как disputed

        if len(article.sources) >= 5:
            # Много источников — обновить
            article.controversy_level = "disputed"
            article.confidence = "MEDIUM"

            # Добавить примечание о конфликте
            article.metadata["conflict_note"] = (
                f"Обнаружен конфликт с {len(conflicts)} статьями. "
                f"Текущий консенсус помечен как спорный."
            )

            self._kb.save_article(article)
            return "обновлено с пометкой 'disputed'"

        else:
            # Мало источников — не добавлять
            return "отклонено из-за конфликтов (мало источников)"