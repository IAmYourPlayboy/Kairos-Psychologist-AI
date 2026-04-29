"""Главный runner агентов — запуск полного пайплайна.

Использование:
    cd backend && python agents/runner.py --topic grief
    cd backend && python agents/runner.py --all
    cd backend && python agents/runner.py --review  # Перепроверка статей
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from typing import Optional

from app.config import settings
from agents.shared.knowledge_base import KnowledgeBase
from agents.shared.pubmed_client import PubMedArticle
from agents.brain.researcher_agent import ResearcherAgent, DEFAULT_TOPICS
from agents.brain.validation_agent import ValidationAgent, TrustLevel
from agents.brain.aggregator_agent import AggregatorAgent, ConsolidatedArticle
from agents.brain.integrator_agent import IntegratorAgent
from agents.brain.orchestrator_agent import OrchestratorAgent, Decision
from agents.brain.module_builder_agent import ModuleBuilderAgent
from agents.brain.re_review_agent import ReReviewAgent

logger = logging.getLogger(__name__)


class AgentRunner:
    """Главный runner для запуска агентов."""

    def __init__(self) -> None:
        """Инициализация."""
        self._kb = KnowledgeBase(base_path=settings.knowledge_base_path)
        self._agents: dict = {}

    async def run_topic(self, topic: str) -> dict:
        """Обработать одну тему.

        Полный пайплайн:
        1. Researcher → ищет статьи
        2. Validation → проверяет качество
        3. Orchestrator → решает что делать
        4. Aggregator → создаёт эталонную статью
        5. Integrator → встраивает в базу
        6. ModuleBuilder → создаёт модуль

        Args:
            topic: Тема для обработки

        Returns:
            Результат выполнения
        """
        logger.info(f"=== Обработка темы: {topic} ===")

        results = {
            "topic": topic,
            "started_at": datetime.now().isoformat(),
            "steps": [],
            "success": False,
        }

        try:
            # 1. Researcher — ищем статьи
            logger.info("Шаг 1: ResearcherAgent...")
            researcher = ResearcherAgent(
                email=settings.pubmed_email,
                llm_provider=None  # Без LLM для MVP
            )

            research_result = await researcher.run({
                "topics": [topic],
                "max_per_topic": 20,
                "date_filter": "365[dp]",
            })

            articles: list[PubMedArticle] = research_result["articles"]
            logger.info(f"Найдено статей: {len(articles)}")

            results["steps"].append({
                "agent": "ResearcherAgent",
                "status": "success",
                "articles_found": len(articles),
            })

            if not articles:
                results["error"] = "Статьи не найдены"
                return results

            # 2. Validation — проверяем качество
            logger.info("Шаг 2: ValidationAgent...")
            validator = ValidationAgent(llm_provider=None)

            validation_results = []
            for article in articles[:10]:  # Проверяем до 10 статей
                result = await validator.run({"article": article})
                validation_results.append(result)

            high_quality = sum(
                1 for r in validation_results
                if r.trust_level in (TrustLevel.HIGH, TrustLevel.MEDIUM)
            )
            logger.info(f"Качественных статей: {high_quality}/{len(validation_results)}")

            results["steps"].append({
                "agent": "ValidationAgent",
                "status": "success",
                "validated": len(validation_results),
                "high_quality": high_quality,
            })

            # 3. Orchestrator — решаем что делать
            logger.info("Шаг 3: OrchestratorAgent...")
            orchestrator = OrchestratorAgent(knowledge_base=self._kb)

            existing = self._kb.search_by_tag(topic)
            orchestrator_result = await orchestrator.run({
                "validation_results": validation_results,
                "topic": topic,
                "existing_articles": existing,
            })

            decision = orchestrator_result["decision"]
            logger.info(f"Решение: {decision.value}")

            results["steps"].append({
                "agent": "OrchestratorAgent",
                "status": "success",
                "decision": decision.value,
                "reasoning": orchestrator_result["reasoning"],
            })

            # 4-6. Выполняем решение Orchestrator
            if decision in (Decision.AGGREGATE, Decision.CREATE_MODULE, Decision.UPDATE_MODULE):
                # Aggregator
                logger.info("Шаг 4: AggregatorAgent...")
                aggregator = AggregatorAgent(llm_provider=None)

                # Фильтруем только качественные статьи
                valid_articles = [
                    articles[i] for i, r in enumerate(validation_results)
                    if r.trust_level != TrustLevel.LOW
                ]

                agg_result = await aggregator.run({
                    "topic": topic,
                    "articles": valid_articles,
                    "existing_article": existing[0] if existing else None,
                })

                article: ConsolidatedArticle = agg_result["article"]

                results["steps"].append({
                    "agent": "AggregatorAgent",
                    "status": "success",
                    "action": agg_result["action"],
                    "article_id": article.id,
                    "confidence": article.confidence,
                })

                # Integrator
                logger.info("Шаг 5: IntegratorAgent...")
                integrator = IntegratorAgent(knowledge_base=self._kb)
                int_result = await integrator.run({
                    "article": article,
                    "check_conflicts": True,
                })

                results["steps"].append({
                    "agent": "IntegratorAgent",
                    "status": int_result["status"],
                    "conflicts": len(int_result["conflicts"]),
                })

                # ModuleBuilder (только если CREATE_MODULE)
                if decision == Decision.CREATE_MODULE:
                    logger.info("Шаг 6: ModuleBuilderAgent...")
                    builder = ModuleBuilderAgent(knowledge_base=self._kb)
                    build_result = await builder.run({
                        "article": article,
                        "create_module": True,
                        "create_skill": True,
                        "update_router": True,
                    })

                    results["steps"].append({
                        "agent": "ModuleBuilderAgent",
                        "status": "success" if build_result["module_created"] else "skipped",
                        "files": build_result["files"],
                    })

            elif decision == Decision.REQUEST_MORE_DATA:
                results["steps"].append({
                    "agent": "OrchestratorAgent",
                    "status": "pending",
                    "message": "Нужно больше данных для создания модуля",
                })

            else:  # SKIP
                results["steps"].append({
                    "agent": "OrchestratorAgent",
                    "status": "skipped",
                    "reason": orchestrator_result["reasoning"],
                })

            results["success"] = True
            results["completed_at"] = datetime.now().isoformat()

        except Exception as e:
            logger.exception(f"Ошибка при обработке темы '{topic}'")
            results["error"] = str(e)
            results["success"] = False

        return results

    async def run_all_topics(self) -> dict:
        """Обработать все темы из DEFAULT_TOPICS.

        Returns:
            Результаты для всех тем
        """
        logger.info(f"=== Обработка всех тем ({len(DEFAULT_TOPICS)}) ===")

        results = {
            "total_topics": len(DEFAULT_TOPICS),
            "started_at": datetime.now().isoformat(),
            "topics": {},
            "success_count": 0,
            "error_count": 0,
        }

        for topic in DEFAULT_TOPICS:
            topic_result = await self.run_topic(topic)
            topic_name = topic.replace(" ", "_")

            results["topics"][topic_name] = topic_result

            if topic_result["success"]:
                results["success_count"] += 1
            else:
                results["error_count"] += 1

        results["completed_at"] = datetime.now().isoformat()

        return results

    async def run_review(self) -> dict:
        """Перепроверить статьи с истёкшей датой.

        Returns:
            Результаты перепроверки
        """
        logger.info("=== Перепроверка статей ===")

        re_reviewer = ReReviewAgent(knowledge_base=self._kb)
        result = await re_reviewer.run({})

        logger.info(f"Перепроверено: {result.get('reviewed', 0)} статей")
        logger.info(f"Требуют внимания: {result.get('needs_attention', 0)}")

        return result


async def main_async(args: argparse.Namespace) -> None:
    """Главная асинхронная функция."""
    # Настройка логирования
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    runner = AgentRunner()

    if args.review:
        # Режим перепроверки
        result = await runner.run_review()
        print("\n=== РЕЗУЛЬТАТЫ ПЕРЕПРОВЕРКИ ===")
        print(f"Перепроверено: {result.get('reviewed', 0)}")
        print(f"Обновлено: {result.get('updated', 0)}")
        print(f"Удалено: {result.get('deleted', 0)}")
        print(f"Требуют внимания: {result.get('needs_attention', 0)}")

    elif args.all:
        # Режим обработки всех тем
        result = await runner.run_all_topics()
        print("\n=== РЕЗУЛЬТАТЫ ===")
        print(f"Всего тем: {result['total_topics']}")
        print(f"Успешно: {result['success_count']}")
        print(f"Ошибок: {result['error_count']}")

    elif args.topic:
        # Режим одной темы
        result = await runner.run_topic(args.topic)
        print("\n=== РЕЗУЛЬТАТЫ ===")
        print(f"Тема: {result['topic']}")
        print(f"Успех: {result['success']}")

        if result.get("error"):
            print(f"Ошибка: {result['error']}")
        else:
            for step in result.get("steps", []):
                print(f"  - {step['agent']}: {step['status']}")

    else:
        print("Укажите режим: --topic, --all или --review")
        sys.exit(1)


def main() -> None:
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description="Запуск агентов Кайроса для обработки научных статей"
    )
    parser.add_argument(
        "--topic",
        type=str,
        help="Обработать одну тему (например 'grief')"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Обработать все темы"
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="Перепроверить статьи с истёкшей датой"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Подробный вывод"
    )

    args = parser.parse_args()

    # Запуск
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\nПрервано пользователем")
        sys.exit(0)


if __name__ == "__main__":
    main()
