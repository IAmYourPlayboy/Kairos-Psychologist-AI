"""PerceptionPipeline — оркестратор одного цикла обработки сообщения.

Дизайн: §8 в spec.

Последовательность:
1. Загрузить контекст: история + выжимка досье + текущий mood
2. Вызвать MessageAnalyzer → PerceptionReport
3. Обновить Mood по отчёту
4. Подтянуть факты по folder_hints
5. Собрать main prompt
6. Вызвать основную LLM → reply
7. Вернуть PipelineResult со всеми артефактами

Этот класс НЕ пишет в БД (это работа chat.py — он создаёт Message-записи).
PerceptionPipeline только читает досье и обновляет Mood (Redis).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm.base import Message
from app.core.llm.factory import get_provider
from app.core.perception.analyzer import MessageAnalyzer
from app.core.perception.dossier import DossierService
from app.core.perception.dossier_summary import facts_to_compact_summary
from app.core.perception.mood import MoodService
from app.core.perception.prompt_builder import build_main_prompt
from app.core.perception.types import MoodState, PerceptionReport

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Результат полного цикла. Используется в chat.py для записи в БД."""

    report: PerceptionReport
    mood: MoodState
    reply: str
    response_time_ms: int | None
    prompt_tokens: int | None
    completion_tokens: int | None


class PerceptionPipeline:
    """Оркестратор одного цикла обработки сообщения.

    Stateless: создаётся per-request, принимая db + redis в конструктор.
    """

    def __init__(
        self,
        *,
        db: AsyncSession,
        redis_client,
        analyzer: MessageAnalyzer | None = None,
    ):
        self._db = db
        self._dossier = DossierService(db)
        self._mood = MoodService(redis_client)
        self._analyzer = analyzer or MessageAnalyzer()

    async def process_message(
        self,
        *,
        user_id: str | None,
        session_id: str,
        user_message: str,
        history: list[dict[str, str]],
    ) -> PipelineResult:
        """Полный цикл одного сообщения.

        Args:
            user_id: id пользователя (None для гостя — тогда досье недоступно).
            session_id: id сессии.
            user_message: текст текущего сообщения.
            history: предыдущие реплики [{"role", "content"}, ...].

        Returns:
            PipelineResult.

        Raises:
            AnalyzerError: если анализатор не смог распарсить ответ.
            httpx.HTTPError / RuntimeError: если LLM упал.
        """
        # === Шаг 1: Контекст для анализатора ===
        # Если user_id None (гость) — досье недоступно.
        if user_id:
            top_facts = await self._dossier.top_relevant_facts(user_id, limit=5)
            dossier_summary = facts_to_compact_summary(top_facts)
        else:
            top_facts = []
            dossier_summary = "(пользователь — гость, досье недоступно)"

        # === Шаг 2: Анализатор ===
        report = await self._analyzer.analyze(
            current_message=user_message,
            history=history,
            dossier_summary=dossier_summary,
        )
        logger.info(
            "Perception: session=%s risk=%s emotion=%s theme=%s",
            session_id[:8], report.risk_level,
            report.dominant_emotion, report.theme,
        )

        # === Шаг 3: Обновить Mood ===
        mood = await self._mood.update_from_report(session_id, report)

        # === Шаг 4: Подтянуть релевантные факты по hints ===
        relevant_facts = []
        if user_id and report.folder_hints:
            # Извлекаем уникальные top-level папки из folder_hints
            # (формат "folder/subfolder")
            target_folders = list({
                h.split("/")[0] for h in report.folder_hints
            })
            relevant_facts = await self._dossier.get_facts_by_folders(
                user_id, folders=target_folders,
            )
            # Если ничего не нашли — берём топ
            if not relevant_facts and top_facts:
                relevant_facts = top_facts

        # === Шаг 5: Собрать main prompt ===
        system_prompt = build_main_prompt(
            report=report,
            mood=mood,
            relevant_facts=relevant_facts,
        )

        # === Шаг 6: Вызвать основную LLM ===
        provider = get_provider()
        messages = [Message(role="system", content=system_prompt)]
        for h in history:
            messages.append(Message(role=h["role"], content=h["content"]))
        messages.append(Message(role="user", content=user_message))

        response = await provider.generate(messages)

        # === Шаг 7: Собрать результат ===
        return PipelineResult(
            report=report,
            mood=mood,
            reply=response.text,
            response_time_ms=int(response.response_time_ms),
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
        )
