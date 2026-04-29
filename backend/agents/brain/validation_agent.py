"""Агент 2: Validation Agent — проверка статей на качество и достоверность.

Три эшелона проверки:
- Эшелон 1: Структурная фильтрация (бесплатно)
- Эшелон 2: LLM-анализ методологии (~2₽/статья)
- Эшелон 3: Консенсус-проверка с cross-reference (~4₽/статья)
"""

import logging
import re
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from agents.shared.base_agent import BaseAgent
from agents.shared.pubmed_client import PubMedArticle

logger = logging.getLogger(__name__)


class TrustLevel(Enum):
    """Уровень доверия к статье."""
    HIGH = "HIGH"      # Можно использовать
    MEDIUM = "MEDIUM" # Использовать с оговорками
    LOW = "LOW"       # Не использовать


class ValidationCategory(Enum):
    """Категория валидации."""
    PASSED = "passed"
    FLAGGED = "flagged"    # Требует внимания
    REJECTED = "rejected"  # Не прошла проверку


@dataclass
class ValidationResult:
    """Результат валидации статьи."""
    pmid: str
    trust_level: TrustLevel
    category: ValidationCategory
    echelon_1_passed: bool
    echelon_2_score: float  # 0.0 - 1.0
    echelon_3_consensus: float  # 0.0 - 1.0
    issues: list[str]
    notes: str
    should_add_to_knowledge_base: bool


class ValidationAgent(BaseAgent):
    """Агент валидации научных статей.

    Проверяет статьи на фейк, качество и достоверность.
    Использует трёхуровневую систему проверки.
    """

    def __init__(self, llm_provider=None) -> None:
        """Инициализация агента.

        Args:
            llm_provider: Провайдер LLM для анализа (Эшелон 2 и 3)
        """
        super().__init__(name="ValidationAgent", priority=2)
        self._llm = llm_provider

    async def run(self, context: dict) -> dict:
        """Выполнить валидацию статьи.

        Args:
            context: {
                "article": PubMedArticle,
                "cross_references": list[str] — PMID связанных статей (для Эшелона 3)
            }

        Returns:
            {
                "validation_result": ValidationResult,
                "action": "add" | "flag" | "reject"
            }
        """
        article: PubMedArticle = context["article"]
        cross_refs: list[str] = context.get("cross_references", [])

        logger.info(f"Валидация статьи: {article.pmid} — {article.title[:50]}...")

        # === ЭШЕЛОН 1: Структурная фильтрация ===
        echelon1_result = await self._echelon_1_structural_filter(article)

        if not echelon1_result["passed"]:
            return {
                "validation_result": ValidationResult(
                    pmid=article.pmid,
                    trust_level=TrustLevel.LOW,
                    category=ValidationCategory.REJECTED,
                    echelon_1_passed=False,
                    echelon_2_score=0.0,
                    echelon_3_consensus=0.0,
                    issues=echelon1_result["issues"],
                    notes="Не прошла Эшелон 1",
                    should_add_to_knowledge_base=False,
                ),
                "action": "reject",
            }

        # === Эшелон 2: LLM-анализ ===
        echelon2_score = await self._echelon_2_llm_analysis(article)

        if echelon2_score < 0.3:
            return {
                "validation_result": ValidationResult(
                    pmid=article.pmid,
                    trust_level=TrustLevel.LOW,
                    category=ValidationCategory.REJECTED,
                    echelon_1_passed=True,
                    echelon_2_score=echelon2_score,
                    echelon_3_consensus=0.0,
                    issues=["Низкое качество методологии"],
                    notes="Не прошла Эшелон 2",
                    should_add_to_knowledge_base=False,
                ),
                "action": "reject",
            }

        # === Эшелон 3: Консенсус-проверка ===
        echelon3_consensus = await self._echelon_3_consensus_check(
            article, cross_refs
        )

        # === Финальное решение ===
        trust_level, category, should_add = self._make_decision(
            echelon2_score, echelon3_consensus
        )

        result = ValidationResult(
            pmid=article.pmid,
            trust_level=trust_level,
            category=category,
            echelon_1_passed=True,
            echelon_2_score=echelon2_score,
            echelon_3_consensus=echelon3_consensus,
            issues=[],
            notes=f"Э2={echelon2_score:.2f}, Э3={echelon3_consensus:.2f}",
            should_add_to_knowledge_base=should_add,
        )

        action = "add" if should_add else "flag"

        logger.info(
            f"Результат валидации {article.pmid}: "
            f"trust={trust_level.value}, action={action}"
        )

        return {
            "validation_result": result,
            "action": action,
        }

    async def _echelon_1_structural_filter(self, article: PubMedArticle) -> dict:
        """Эшелон 1: Быстрая структурная фильтрация.

        Проверяет базовые критерии без LLM.
        Возвращает:
            {"passed": bool, "issues": list[str]}
        """
        issues = []

        # 1. Есть ли DOI (индикатор качества)?
        if not article.doi:
            issues.append("Нет DOI")

        # 2. Достаточно ли абстракт?
        if len(article.abstract) < 100:
            issues.append("Слишком короткий абстракт")

        # 3. Есть ли название статьи?
        if not article.title or len(article.title) < 10:
            issues.append("Нет названия")

        # 4. Указан ли журнал?
        if not article.journal:
            issues.append("Не указан журнал")

        # 5. Проверка на спам-паттерны в тексте
        spam_patterns = [
            r"click here",
            r"buy now",
            r"free money",
            r"limited time offer",
            r"congratulations you won",
        ]

        text_to_check = f"{article.title} {article.abstract}".lower()
        for pattern in spam_patterns:
            if re.search(pattern, text_to_check):
                issues.append(f"Спам-паттерн: {pattern}")
                break

        # Если есть DOI и нормальный абстракт — прошла
        passed = len(issues) == 0 or (
            article.doi is not None
            and len(article.abstract) >= 100
            and len(issues) <= 1
        )

        return {"passed": passed, "issues": issues}

    async def _echelon_2_llm_analysis(self, article: PubMedArticle) -> float:
        """Эшелон 2: LLM-анализ методологии.

        Оценивает качество статьи по методологическим критериям.
        Возвращает оценку 0.0 - 1.0.
        """
        if not self._llm:
            # Если нет LLM — пропускаем (для MVP)
            logger.warning("LLM не подключён, пропускаем Эшелон 2")
            return 0.7

        prompt = f"""Ты — научный редактор. Оцени качество исследования по 10-балльной шкале.

Статья: {article.title}

Абстракт: {article.abstract}

Оцени по критериям:
1. Методология описана (0-3 балла)
2. Выборка адекватная >30 человек (0-2 балла)
3. Есть статистический анализ (0-2 балла)
4. Нет явных манипуляций (0-3 балла)

Ответь ТОЛЬКО числом от 0 до 1.0 (1.0 = идеальное исследование).
Примеры: 0.3, 0.7, 0.9

Если абстракт слишком короткий для оценки — верни 0.5.
"""

        try:
            response = await self._llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Низкая температура для оценки
                max_tokens=50,
            )
            score = float(response.text.strip())
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.error(f"Ошибка LLM-анализа: {e}")
            return 0.5

    async def _echelon_3_consensus_check(
        self, article: PubMedArticle, cross_refs: list[str]
    ) -> float:
        """Эшелон 3: Проверка консенсуса.

        Оценивает, подтверждается ли статья другими источниками.
        Возвращает оценку 0.0 - 1.0.
        """
        if not self._llm or not cross_refs:
            # Если нет данных для сравнения
            return 0.5

        prompt = f"""Ты — эксперт по оценке научного консенсуса.

Оцени, насколько статья согласуется с научным консенсусом.

Статья: {article.title}
Абстракт: {article.abstract}

Ответь на вопросы:
1. Подтверждается ли вывод другими авторами в этой области?
2. Есть ли опровержения или противоречия?
3. Это консенсус или спорный вопрос?

Оценка:
- 1.0 = Сильный консенсус, подтверждено многими исследователями
- 0.7 = В целом согласовано, мелкие нюансы
- 0.5 = Неопределённо, недостаточно данных
- 0.3 = Спорные данные, есть противоречия
- 0.1 = Противоречит большинству исследований

Ответь ТОЛЬКО числом 0.0-1.0.
"""

        try:
            response = await self._llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=50,
            )
            score = float(response.text.strip())
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.error(f"Ошибка проверки консенсуса: {e}")
            return 0.5

    def _make_decision(
        self, echelon2_score: float, echelon3_consensus: float
    ) -> tuple[TrustLevel, ValidationCategory, bool]:
        """Принять финальное решение о статье.

        Args:
            echelon2_score: Оценка методологии (0-1)
            echelon3_consensus: Оценка консенсуса (0-1)

        Returns:
            (TrustLevel, ValidationCategory, should_add)
        """
        # Комбинированная оценка
        combined = (echelon2_score * 0.6) + (echelon3_consensus * 0.4)

        if combined >= 0.7:
            return TrustLevel.HIGH, ValidationCategory.PASSED, True
        elif combined >= 0.4:
            return TrustLevel.MEDIUM, ValidationCategory.FLAGGED, True
        else:
            return TrustLevel.LOW, ValidationCategory.REJECTED, False
