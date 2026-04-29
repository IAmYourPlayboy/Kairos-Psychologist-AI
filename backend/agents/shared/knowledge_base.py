"""Менеджер базы знаний Кайроса.

Хранит и управляет эталонными агрегированными статьями.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import yaml

from agents.brain.aggregator_agent import ConsolidatedArticle

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """База знаний Кайроса.

    Хранит эталонные агрегированные статьи в файловой системе.
    Для MVP — простая структура, масштабируется до PostgreSQL/Qdrant later.
    """

    def __init__(self, base_path: str = "knowledge_base") -> None:
        """
        Args:
            base_path: Путь к папке с базой знаний
        """
        self._base_path = Path(base_path)
        self._psychology_path = self._base_path / "psychology"
        self._culture_path = self._base_path / "culture"

        # Создать папки если их нет
        self._psychology_path.mkdir(parents=True, exist_ok=True)
        self._culture_path.mkdir(parents=True, exist_ok=True)

    def save_article(self, article: ConsolidatedArticle) -> str:
        """Сохранить эталонную статью.

        Args:
            article: ConsolidatedArticle для сохранения

        Returns:
            Путь к сохранённому файлу
        """
        # Создать папку для темы
        topic_path = self._psychology_path / article.topic
        topic_path.mkdir(parents=True, exist_ok=True)

        # Путь к файлу
        file_path = topic_path / f"{article.id}.yaml"

        # Конвертировать в словарь
        article_dict = {
            "id": article.id,
            "title": article.title,
            "topic": article.topic,
            "consensus": article.consensus,
            "nuances": article.nuances,
            "story": article.story,
            "sources": [
                {
                    "name": s.name,
                    "full_name": s.full_name,
                    "reference": s.reference,
                    "contribution": s.contribution,
                    "tags": s.tags,
                }
                for s in article.sources
            ],
            "confidence": article.confidence,
            "controversy_level": article.controversy_level,
            "created_at": article.created_at.isoformat(),
            "last_reviewed": article.last_reviewed.isoformat(),
            "next_review": article.next_review.isoformat(),
            "tags": article.tags,
            "related_articles": article.related_articles,
            "metadata": article.metadata,
        }

        # Сохранить как YAML
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(article_dict, f, allow_unicode=True, default_flow_style=False)

        logger.info(f"Сохранена статья: {file_path}")
        return str(file_path)

    def load_article(self, article_id: str, topic: str) -> Optional[ConsolidatedArticle]:
        """Загрузить эталонную статью.

        Args:
            article_id: ID статьи
            topic: Тема статьи

        Returns:
            ConsolidatedArticle или None если не найдена
        """
        file_path = self._psychology_path / topic / f"{article_id}.yaml"

        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Восстановить объект
        sources = [
            {
                "name": s["name"],
                "full_name": s["full_name"],
                "reference": s["reference"],
                "contribution": s["contribution"],
                "tags": s["tags"],
            }
            for s in data.get("sources", [])
        ]

        article = ConsolidatedArticle(
            id=data["id"],
            title=data["title"],
            topic=data["topic"],
            consensus=data["consensus"],
            nuances=data["nuances"],
            story=data["story"],
            sources=sources,
            confidence=data["confidence"],
            controversy_level=data["controversy_level"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_reviewed=datetime.fromisoformat(data["last_reviewed"]),
            next_review=datetime.fromisoformat(data["next_review"]),
            tags=data.get("tags", []),
            related_articles=data.get("related_articles", []),
            metadata=data.get("metadata", {}),
        )

        return article

    def get_articles_for_review(self) -> list[ConsolidatedArticle]:
        """Получить статьи, требующие перепроверки.

        Returns:
            Список статей с истёкшей датой next_review
        """
        articles = []
        now = datetime.now()

        for topic_dir in self._psychology_path.iterdir():
            if topic_dir.is_dir():
                for file_path in topic_dir.glob("*.yaml"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)

                        next_review = datetime.fromisoformat(data["next_review"])
                        if next_review <= now:
                            # Статья требует перепроверки
                            article = self.load_article(data["id"], data["topic"])
                            if article:
                                articles.append(article)

                    except Exception as e:
                        logger.warning(f"Ошибка чтения {file_path}: {e}")
                        continue

        return articles

    def search_by_tag(self, tag: str) -> list[ConsolidatedArticle]:
        """Найти статьи по тегу.

        Args:
            tag: Тег для поиска

        Returns:
            Список статей с этим тегом
        """
        articles = []

        for topic_dir in self._psychology_path.iterdir():
            if topic_dir.is_dir():
                for file_path in topic_dir.glob("*.yaml"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)

                        if tag in data.get("tags", []):
                            article = self.load_article(data["id"], data["topic"])
                            if article:
                                articles.append(article)

                    except Exception:
                        continue

        return articles

    def search_by_source_tag(self, source_tag: str) -> list[ConsolidatedArticle]:
        """Найти статьи, использующие конкретный источник.

        Для ответа "почему ты так считаешь?" — найти все статьи,
        где source.name == source_tag.

        Args:
            source_tag: Тег источника (например "[Worden]")

        Returns:
            Список статей с этим источником
        """
        articles = []

        for topic_dir in self._psychology_path.iterdir():
            if topic_dir.is_dir():
                for file_path in topic_dir.glob("*.yaml"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)

                        for source in data.get("sources", []):
                            if source["name"] == source_tag:
                                article = self.load_article(data["id"], data["topic"])
                                if article:
                                    articles.append(article)
                                break

                    except Exception:
                        continue

        return articles

    def get_all_topics(self) -> list[str]:
        """Получить список всех тем."""
        topics = []
        for topic_dir in self._psychology_path.iterdir():
            if topic_dir.is_dir():
                topics.append(topic_dir.name)
        return sorted(topics)

    def list_articles(self, topic: Optional[str] = None) -> list[dict]:
        """Список всех статей.

        Args:
            topic: Фильтр по теме (опционально)

        Returns:
            Список метаданных статей
        """
        articles = []

        if topic:
            paths = [self._psychology_path / topic]
        else:
            paths = list(self._psychology_path.iterdir())

        for topic_dir in paths:
            if topic_dir.is_dir():
                for file_path in topic_dir.glob("*.yaml"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)

                        articles.append({
                            "id": data["id"],
                            "title": data["title"],
                            "topic": data["topic"],
                            "confidence": data["confidence"],
                            "controversy_level": data["controversy_level"],
                            "last_reviewed": data["last_reviewed"],
                            "next_review": data["next_review"],
                            "sources_count": len(data.get("sources", [])),
                        })

                    except Exception:
                        continue

        return articles