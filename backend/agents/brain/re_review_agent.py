"""Агент 9: ReReview Agent — перепроверка статей.

Автоматическая перепроверка эталонных статей:
- Первая проверка: через 3 месяца
- Последующие: каждые 6 месяцев
"""

import logging
from datetime import datetime, timedelta

from agents.shared.base_agent import BaseAgent
from agents.shared.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class ReReviewAgent(BaseAgent):
    """Агент перепроверки статей.

    Периодически проверяет статьи на актуальность:
    - Retraction Watch
    - Новые опровержения
    - Обновление консенсуса
    """

    def __init__(self, knowledge_base: KnowledgeBase, llm_provider=None) -> None:
        """Инициализация.

        Args:
            knowledge_base: База знаний
            llm_provider: LLM для анализа новых данных
        """
        super().__init__(name="ReReviewAgent", priority=9)
        self._kb = knowledge_base
        self._llm = llm_provider

    async def run(self, context: dict) -> dict:
        """Запустить перепроверку.

        Args:
            context: {
                "article_ids": list[str] — конкретные статьи (опционально),
                "all_overdue": bool = True — проверить все просроченные
            }

        Returns:
            {
                "reviewed": list[dict],
                "updated": list[str],
                "deleted": list[str],
                "errors": list[str]
            }
        """
        article_ids = context.get("article_ids", [])
        all_overdue = context.get("all_overdue", True)

        result = {
            "reviewed": [],
            "updated": [],
            "deleted": [],
            "errors": [],
        }

        # Получить статьи для проверки
        if all_overdue:
            articles_to_review = self._kb.get_articles_for_review()
        elif article_ids:
            articles_to_review = []
            for article_id in article_ids:
                # Нужно знать topic для загрузки
                # Пока упрощённо
                pass
        else:
            articles_to_review = []

        logger.info(f"Перепроверка: {len(articles_to_review)} статей")

        for article in articles_to_review:
            try:
                review_result = await self._review_article(article)

                result["reviewed"].append({
                    "id": article.id,
                    "status": review_result["status"],
                    "reason": review_result["reason"],
                })

                if review_result["status"] == "updated":
                    result["updated"].append(article.id)
                elif review_result["status"] == "deleted":
                    result["deleted"].append(article.id)

            except Exception as e:
                logger.error(f"Ошибка перепроверки {article.id}: {e}")
                result["errors"].append(f"{article.id}: {str(e)}")

        logger.info(
            f"Перепроверка завершена: "
            f"{len(result['updated'])} обновлено, "
            f"{len(result['deleted'])} удалено, "
            f"{len(result['errors'])} ошибок"
        )

        return result

    async def _review_article(self, article) -> dict:
        """Перепроверить одну статью.

        Проверяет:
        1. Retraction Watch
        2. Новые опровержения
        3. Актуальность консенсуса
        4. Обновить или удалить
        """
        # Проверка на Retraction Watch
        is_retracted = await self._check_retraction(article)

        if is_retracted:
            return {
                "status": "deleted",
                "reason": "Статья в Retraction Watch",
            }

        # Проверка новых данных через LLM
        has_new_data = await self._check_new_evidence(article)

        if has_new_data:
            # Обновить статью
            await self._update_article(article)
            return {
                "status": "updated",
                "reason": "Найдены новые данные, консенсус обновлён",
            }

        # Просто обновить дату следующей проверки (через 6 месяцев)
        article.next_review = datetime.now() + timedelta(days=180)
        self._kb.save_article(article)

        return {
            "status": "ok",
            "reason": "Актуально, следующая проверка через 6 месяцев",
        }

    async def _check_retraction(self, article) -> bool:
        """Проверить статью в Retraction Watch."""
        # TODO: Интеграция с Retraction Watch API
        # Пока заглушка
        return False

    async def _check_new_evidence(self, article) -> bool:
        """Проверить наличие новых опровержений или данных.

        Использует PubMed для поиска новых статей по теме.
        """
        if not self._llm:
            return False

        # Поиск новых статей по теме
        # Если есть значимые противоречия → обновить

        return False  # Пока не реализовано

    async def _update_article(self, article) -> None:
        """Обновить статью с новыми данными."""
        # Пересчитать консенсус
        # Обновить sources
        # Изменить controversy_level если нужно

        article.last_reviewed = datetime.now()

        # Пересчитать следующую проверку
        if article.next_review and article.last_reviewed:
            # Была первая проверка (3 мес), теперь 6 мес
            article.next_review = datetime.now() + timedelta(days=180)

        self._kb.save_article(article)