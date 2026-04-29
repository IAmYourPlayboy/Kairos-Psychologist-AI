"""Агент 1: Researcher Agent — поиск статей на PubMed."""

import logging
from typing import Optional

from agents.shared.base_agent import BaseAgent
from agents.shared.pubmed_client import PubMedClient, PubMedArticle

logger = logging.getLogger(__name__)


# Темы для MVP (10 штук)
DEFAULT_TOPICS = [
    "grief bereavement mourning",
    "crisis intervention psychological first aid",
    "depression mental health treatment",
    "anxiety disorder therapy",
    "PTSD trauma therapy",
    "suicidal ideation risk assessment",
    "family crisis therapy",
    "child psychology development",
    "post-traumatic stress treatment",
    "emotional regulation DBT",
]


class ResearcherAgent(BaseAgent):
    """Агент поиска научных статей.

    Ищет статьи на PubMed по заданным темам.
    Поддерживает приоритетные запросы от Orchestrator.
    """

    def __init__(self, email: str, llm_provider=None) -> None:
        """Инициализация.

        Args:
            email: Email для PubMed API
            llm_provider: LLM для улучшения поисковых запросов
        """
        super().__init__(name="ResearcherAgent", priority=1)
        self._pubmed = PubMedClient(email=email)
        self._llm = llm_provider

    async def run(self, context: dict) -> dict:
        """Найти статьи по теме.

        Args:
            context: {
                "topics": list[str] — темы для поиска (опционально),
                "priority_query": str — приоритетный запрос от Orchestrator (опционально),
                "max_per_topic": int = 20,
                "date_filter": str = "365[dp]" — статьи за последний год
            }

        Returns:
            {
                "articles": list[PubMedArticle],
                "topic": str,
                "search_stats": dict
            }
        """
        topics = context.get("topics", DEFAULT_TOPICS)
        priority_query = context.get("priority_query")
        max_per_topic = context.get("max_per_topic", 20)
        date_filter = context.get("date_filter", "365[dp]")

        all_articles = []
        stats = {"topics_searched": 0, "articles_found": 0, "errors": []}

        # Если есть приоритетный запрос — ищем сначала его
        if priority_query:
            logger.info(f"Поиск приоритетного запроса: {priority_query}")
            priority_articles = await self._search_topic(
                priority_query, max_per_topic, date_filter
            )
            all_articles.extend(priority_articles)
            stats["priority_articles"] = len(priority_articles)

        # Поиск по основным темам
        for topic in topics:
            try:
                articles = await self._search_topic(
                    topic, max_per_topic, date_filter
                )
                all_articles.extend(articles)
                stats["topics_searched"] += 1
                stats["articles_found"] += len(articles)

                logger.info(f"Тема '{topic}': найдено {len(articles)} статей")

            except Exception as e:
                logger.error(f"Ошибка поиска по теме '{topic}': {e}")
                stats["errors"].append(f"{topic}: {str(e)}")

        # Убрать дубликаты по PMID
        seen_pmids = set()
        unique_articles = []
        for article in all_articles:
            if article.pmid not in seen_pmids:
                seen_pmids.add(article.pmid)
                unique_articles.append(article)

        logger.info(
            f"Итого: {stats['topics_searched']} тем, "
            f"{len(unique_articles)} уникальных статей"
        )

        return {
            "articles": unique_articles,
            "stats": stats,
        }

    async def _search_topic(
        self, query: str, max_results: int, date_filter: str
    ) -> list[PubMedArticle]:
        """Поиск статей по одной теме.

        Args:
            query: Поисковый запрос
            max_results: Максимум результатов
            date_filter: Фильтр по дате

        Returns:
            Список статей
        """
        # Улучшить запрос через LLM (опционально)
        if self._llm:
            query = await self._improve_query(query)

        # Поиск PMID
        pmids = await self._pubmed.search(
            query=query,
            max_results=max_results,
            date_filter=date_filter,
        )

        if not pmids:
            return []

        # Получить детали статей
        articles = await self._pubmed.fetch_articles(pmids)

        return articles

    async def _improve_query(self, query: str) -> str:
        """Улучшить поисковый запрос через LLM.

        Конвертирует естественный язык в PubMed-совместимый запрос.
        """
        if not self._llm:
            return query

        prompt = f"""Преобразуй этот поисковый запрос в формат PubMed E-utilities.

Требования:
- Используй булевы операторы (AND, OR)
- Добавляй Medical Subject Headings (MeSH terms)
- Формат: термин[tiab] для поиска в заголовке и абстракте

Пример:
Вход: "лечение тревоги у подростков"
Выход: "anxiety[tiab] AND treatment[tiab] AND adolescent[MeSH Terms]"

Вход: "{query}"
Выход:"""

        try:
            response = await self._llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200,
            )
            improved = response.text.strip()
            logger.debug(f"Улучшенный запрос: {improved}")
            return improved if improved else query
        except Exception as e:
            logger.warning(f"Не удалось улучшить запрос: {e}")
            return query

    async def close(self) -> None:
        """Закрыть клиенты."""
        await self._pubmed.close()
