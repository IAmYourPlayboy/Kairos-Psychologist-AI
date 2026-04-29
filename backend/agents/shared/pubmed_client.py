"""PubMed API клиент для поиска научных статей."""

import logging
from typing import Optional
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)


@dataclass
class PubMedArticle:
    """Структура статьи из PubMed."""
    pmid: str
    title: str
    abstract: str
    authors: list[str]
    journal: str
    publication_date: str
    doi: Optional[str]
    mesh_terms: list[str]


class PubMedClient:
    """Клиент для PubMed API (E-utilities).

    Бесплатный API для поиска в базе PubMed.
    Документация: https://eutils.ncbi.nlm.nih.gov/homepage/api.html
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, email: str) -> None:
        """
        Args:
            email: Email для идентификации (обязательно для PubMed)
        """
        self._email = email
        self._client = httpx.AsyncClient(timeout=30.0)

    async def search(
        self,
        query: str,
        max_results: int = 50,
        date_filter: Optional[str] = None,
    ) -> list[str]:
        """Поиск статей по запросу.

        Args:
            query: Поисковый запрос (PMC/PubMed синтаксис)
            max_results: Максимум результатов
            date_filter: Фильтр по дате (например "10[dp]")

        Returns:
            Список PMID найденных статей
        """
        # Формируем запрос
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
            "email": self._email,
        }

        if date_filter:
            search_params["datetype"] = "pdat"
            search_params["reldate"] = date_filter

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/esearch.fcgi",
                params=search_params,
            )
            response.raise_for_status()
            data = response.json()

            id_list = data.get("esearchresult", {}).get("idlist", [])
            logger.info(f"Найдено {len(id_list)} статей по запросу: {query}")
            return id_list

        except httpx.HTTPError as e:
            logger.error(f"Ошибка поиска PubMed: {e}")
            return []

    async def fetch_articles(self, pmids: list[str]) -> list[PubMedArticle]:
        """Получить детали статей по PMID.

        Args:
            pmids: Список PMID

        Returns:
            Список объектов PubMedArticle
        """
        if not pmids:
            return []

        # EFetch для получения деталей
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/efetch.fcgi",
                params=params,
            )
            response.raise_for_status()
            # Парсинг XML (упрощённый)
            articles = self._parse_xml(response.text)
            return articles

        except httpx.HTTPError as e:
            logger.error(f"Ошибка получения статей: {e}")
            return []

    def _parse_xml(self, xml: str) -> list[PubMedArticle]:
        """Парсинг XML ответа PubMed.

        Упрощённый парсер для извлечения основных полей.
        Для production можно использовать lxml или beautifulsoup.
        """
        import re

        articles = []
        # Упрощённый regex-парсинг (для MVP)
        # В production заменить на proper XML parsing

        # Разбиваем по Article
        article_blocks = re.split(r'<PubmedArticle>', xml)
        article_blocks = [b for b in article_blocks if '<PMID' in b]

        for block in article_blocks:
            try:
                pmid = re.search(r'<PMID[^>]*>([^<]+)</PMID>', block)
                title = re.search(r'<ArticleTitle>([^<]+)</ArticleTitle>', block)
                abstract = re.search(r'<AbstractText[^>]*>([^<]*)</AbstractText>', block)
                journal = re.search(r'<Journal><Title>([^<]+)</Title>', block)
                date = re.search(r'<PubDate>.*?<Year>([^<]+)</Year>', block)
                doi = re.search(r'<ArticleId IdType="doi">([^<]+)</ArticleId>', block)

                if pmid and title:
                    article = PubMedArticle(
                        pmid=pmid.group(1),
                        title=title.group(1) if title else "",
                        abstract=abstract.group(1) if abstract else "",
                        authors=[],  # Упрощено
                        journal=journal.group(1) if journal else "",
                        publication_date=date.group(1) if date else "",
                        doi=doi.group(1) if doi else None,
                        mesh_terms=[],
                    )
                    articles.append(article)

            except Exception as e:
                logger.warning(f"Ошибка парсинга статьи: {e}")
                continue

        return articles

    async def check_retraction(self, pmid: str) -> bool:
        """Проверить, отозвана ли статья.

        Args:
            pmid: PMID статьи

        Returns:
            True если статья отозвана
        """
        # Проверяем через PubMed статус
        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml",
        }

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/efetch.fcgi",
                params=params,
            )
            response.raise_for_status()

            # Проверяем PublicationStatus
            if "Retracted" in response.text or "Retraction" in response.text:
                return True

            return False

        except httpx.HTTPError:
            return False

    async def get_journal_impact(self, journal_name: str) -> dict:
        """Получить информацию о журнале.

        Пока заглушка — требует отдельного API (Scopus/WoS).

        Args:
            journal_name: Название журнала

        Returns:
            Информация о журнале
        """
        # TODO: Интеграция с Scopus API или NLM Journal Catalog
        return {
            "name": journal_name,
            "impact_factor": None,
            "peer_reviewed": True,  # По умолчанию для PubMed
            "indexed": True,
        }

    async def close(self) -> None:
        """Закрыть HTTP-клиент."""
        await self._client.aclose()
