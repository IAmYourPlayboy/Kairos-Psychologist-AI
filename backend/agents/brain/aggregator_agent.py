"""Агент 3: Aggregator Agent — создание эталонных агрегированных статей.

Создаёт единый документ из множества источников с:
- Консенсусом (что согласовано между авторами)
- Нюансами (разногласия между авторами)
- Сторителлингом (объяснение для пользователя простым языком)
- Метаданными для ответа "почему ты так считаешь?"
"""

import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from agents.shared.base_agent import BaseAgent
from agents.shared.pubmed_client import PubMedArticle

logger = logging.getLogger(__name__)


@dataclass
class Source:
    """Источник информации."""
    name: str              # Короткое имя для тега: "[Worden]"
    full_name: str         # Полное имя автора
    reference: str         # Полная библиография
    contribution: str      # Что внёс этот автор
    tags: list[str]        # Теги для поиска


@dataclass
class ConsolidatedArticle:
    """Эталонная агрегированная статья.

    Объединяет знания из множества источников в один документ.
    """
    id: str
    title: str
    topic: str                    # Тема (grief, crisis, trauma...)
    consensus: str                # Основные выводы
    nuances: str                  # Разногласия между авторами
    story: str                    # Сторителлинг для пользователя
    sources: list[Source]         # Источники
    confidence: str               # "HIGH" | "MEDIUM" | "LOW"
    controversy_level: str         # "consensus" | "disputed" | "unclear"
    created_at: datetime
    last_reviewed: datetime
    next_review: datetime         # 3 месяца для первой проверки
    tags: list[str]               # Для поиска
    related_articles: list[str]   # ID связанных статей
    metadata: dict = field(default_factory=dict)


class AggregatorAgent(BaseAgent):
    """Агент агрегации научных знаний.

    Создаёт эталонные статьи из множества источников.
    Ключевая фишка: поле `story` с объяснением в стиле сторителлинга.
    """

    def __init__(self, llm_provider=None) -> None:
        """Инициализация.

        Args:
            llm_provider: LLM для генерации сторителлинга
        """
        super().__init__(name="AggregatorAgent", priority=3)
        self._llm = llm_provider

    async def run(self, context: dict) -> dict:
        """Создать эталонную статью из списка статей.

        Args:
            context: {
                "topic": str,                    # Тема статьи
                "articles": list[PubMedArticle], # Исходные статьи
                "existing_article": Optional[ConsolidatedArticle] = None  # Для обновления
            }

        Returns:
            {
                "article": ConsolidatedArticle,
                "action": "create" | "update"
            }
        """
        topic: str = context["topic"]
        articles: list[PubMedArticle] = context["articles"]
        existing: Optional[ConsolidatedArticle] = context.get("existing_article")

        logger.info(
            f"Агрегация {len(articles)} статей по теме: {topic}"
        )

        # Сгенерировать сторителлинг через LLM
        story = await self._generate_story(topic, articles)

        # Создать структуру sources
        sources = self._create_sources(articles)

        # Определить консенсус и нюансы
        consensus, nuances = await self._analyze_consensus(articles)

        # Определить controversy_level
        controversy = self._determine_controversy(consensus, nuances)

        # Создать или обновить статью
        if existing:
            # Обновить существующую
            article = self._update_article(existing, sources, consensus, nuances, story)
            action = "update"
        else:
            # Создать новую
            article = self._create_article(topic, sources, consensus, nuances, story)
            action = "create"

        logger.info(f"Создана эталонная статья: {article.id}")

        return {
            "article": article,
            "action": action,
        }

    async def _generate_story(
        self, topic: str, articles: list[PubMedArticle]
    ) -> str:
        """Сгенерировать сторителлинг для объяснения темы пользователю.

        Использует LLM для создания текста в стиле "Жила-была женщина..."
        """
        if not self._llm:
            # Fallback — простой текст
            return self._generate_fallback_story(topic, articles)

        # Собрать информацию о ключевых авторах
        authors_context = self._extract_authors_context(articles)

        prompt = f"""Ты — научный популяризатор. Объясни тему "{topic}" простым языком в стиле сторителлинга.

Правила:
1. Начинай с истории человека/людей, которые открыли/создали эту концепцию
2. Используй "Жила-была...", "Давным-давно...", "Однажды..."
3. Объясни ПОЧЕМУ это важно, не только ЧТО это такое
4. Имена собственные — полностью (не аббревиатуры)
5. Научные термины — объясняй просто
6. Конец: свяжи с реальной жизнью слушателя

Пример стиля:
"Жила-была женщина из Франции, звали её Элизабет Кюблер-Росс.
Всю жизнь она работала с умирающими пациентами в госпитале и
однажды поняла, что смерть — это не просто конец, а целый процесс,
который люди проходят по-своему..."

Контекст по теме:
{authors_context}

Напиши текст на 3-4 абзаца. Для российской аудитории."""

        try:
            response = await self._llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,  # Креативность для сторителлинга
                max_tokens=2000,
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Ошибка генерации сторителлинга: {e}")
            return self._generate_fallback_story(topic, articles)

    def _extract_authors_context(self, articles: list[PubMedArticle]) -> str:
        """Извлечь контекст об авторах из статей."""
        contexts = []

        for article in articles[:5]:  # Берём первые 5 статей
            contexts.append(
                f"- {article.title[:100]}\n"
                f"  Журнал: {article.journal}\n"
                f"  Дата: {article.publication_date}\n"
                f"  Аннотация: {article.abstract[:200]}..."
            )

        return "\n\n".join(contexts)

    def _generate_fallback_story(self, topic: str, articles: list[PubMedArticle]) -> str:
        """Fallback если LLM недоступен."""
        # Простой сторителлинг на основе заголовков
        main_article = articles[0] if articles else None

        if main_article:
            return (
                f"Эта тема ({topic}) основана на научных исследованиях. "
                f"Одно из ключевых исследований — работа «{main_article.title[:100]}...», "
                f"опубликованная в журнале {main_article.journal}. "
                f"Подробности доступны в полной версии эталонной статьи."
            )

        return f"Информация по теме '{topic}' основана на научных исследованиях."

    def _create_sources(self, articles: list[PubMedArticle]) -> list[Source]:
        """Создать список источников из статей."""
        sources = []

        for i, article in enumerate(articles[:10]):  # Максимум 10 источников
            # Генерируем короткое имя
            name = f"[Источник_{i+1}]"

            source = Source(
                name=name,
                full_name=article.authors[0] if article.authors else "Неизвестный автор",
                reference=f"{article.title}. {article.journal}. {article.publication_date}. DOI: {article.doi or 'N/A'}",
                contribution="Внесён вклад в тему",  # Упрощено
                tags=article.mesh_terms[:5] if article.mesh_terms else [],
            )
            sources.append(source)

        return sources

    async def _analyze_consensus(
        self, articles: list[PubMedArticle]
    ) -> tuple[str, str]:
        """Проанализировать консенсус и разногласия между статьями.

        Returns:
            (consensus, nuances)
        """
        if not self._llm:
            # Fallback
            consensus = (
                f"Основано на {len(articles)} научных источниках. "
                f"Требуется ручной анализ для детального консенсуса."
            )
            nuances = "Требуется экспертная оценка разногласий."
            return consensus, nuances

        # Собрать все абстракты
        abstracts = "\n\n".join([
            f"Статья {i+1}: {a.abstract[:500]}" for i, a in enumerate(articles[:5])
        ])

        prompt = f"""Проанализируй эти научные статьи и определи:

1. КОНСЕНСУС: Что согласовано между авторами? Общие выводы?

2. НЮАНСЫ: В чём авторы расходятся? Какие есть разногласия?

Формат ответа:
КОНСЕНСУС:
[Текст консенсуса в 2-3 предложениях]

НЮАНСЫ:
[Текст о разногласиях в 2-3 предложениях]

Статьи:
{abstracts}"""

        try:
            response = await self._llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )

            text = response.text
            consensus = ""
            nuances = ""

            if "КОНСЕНСУС:" in text:
                parts = text.split("НЮАНСЫ:")
                if len(parts) == 2:
                    consensus = parts[0].replace("КОНСЕНСУС:", "").strip()
                    nuances = parts[1].strip()

            return consensus or "Требуется анализ", nuances or "Требуется анализ"

        except Exception as e:
            logger.error(f"Ошибка анализа консенсуса: {e}")
            return "Требуется анализ", "Требуется анализ"

    def _determine_controversy(self, consensus: str, nuances: str) -> str:
        """Определить уровень спорности темы."""
        if "расход" in nuances.lower() or "спор" in nuances.lower():
            return "disputed"
        elif "согласова" in consensus.lower() and len(nuances) < 50:
            return "consensus"
        else:
            return "unclear"

    def _create_article(
        self,
        topic: str,
        sources: list[Source],
        consensus: str,
        nuances: str,
        story: str,
    ) -> ConsolidatedArticle:
        """Создать новую эталонную статью."""
        from datetime import timedelta

        now = datetime.now()
        next_review = now + timedelta(days=90)  # 3 месяца

        article = ConsolidatedArticle(
            id=f"ca_{topic}_{now.strftime('%Y%m%d')}",
            title=f"{topic}: научный консенсус",
            topic=topic,
            consensus=consensus,
            nuances=nuances,
            story=story,
            sources=sources,
            confidence="MEDIUM",  # На старте Medium, потом может вырасти
            controversy_level=self._determine_controversy(consensus, nuances),
            created_at=now,
            last_reviewed=now,
            next_review=next_review,
            tags=[topic.lower()],
            related_articles=[],
        )

        return article

    def _update_article(
        self,
        existing: ConsolidatedArticle,
        sources: list[Source],
        consensus: str,
        nuances: str,
        story: str,
    ) -> ConsolidatedArticle:
        """Обновить существующую эталонную статью."""
        from datetime import timedelta

        now = datetime.now()
        next_review = now + timedelta(days=180)  # 6 месяцев для последующих проверок

        # Сохраняем старые источники, добавляем новые
        all_sources = existing.sources + sources
        # Убираем дубликаты по имени
        seen_names = set()
        unique_sources = []
        for s in all_sources:
            if s.name not in seen_names:
                seen_names.add(s.name)
                unique_sources.append(s)

        existing.consensus = consensus
        existing.nuances = nuances
        existing.story = story
        existing.sources = unique_sources[:20]  # Максимум 20 источников
        existing.last_reviewed = now
        existing.next_review = next_review

        # Пересчитать confidence
        if len(unique_sources) >= 5:
            existing.confidence = "HIGH"

        return existing