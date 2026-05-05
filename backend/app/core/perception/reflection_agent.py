"""ReflectionAgent — фоновый агент извлечения фактов из разговоров.

Дизайн: §7 в spec.

Полный цикл (run_for_user):
1. Прочитать чекпойнт пользователя.
2. Загрузить все сообщения пользователя ПОСЛЕ checkpoint_message_id.
3. Если ничего нового — выйти.
4. Extract: один LLM-вызов → массив фактов-кандидатов.
5. Classify+Dedupe: для каждого кандидата — найти существующие факты
   в той же папке, решить (merge / create_new / supersede).
6. Update: применить решения через DossierService.
7. Сдвинуть чекпойнт.

Не зависит от Celery — Celery просто оборачивает run_for_user в таск
(см. reflection_tasks.py).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm.base import Message as LLMMessage
from app.core.llm.factory import get_provider
from app.core.perception.analyzer import strip_markdown_fence
from app.core.perception.dossier import DossierService
from app.core.perception.dossier_summary import facts_to_compact_summary
from app.core.perception.folders import is_valid_subfolder
from app.core.perception.reflection_prompt import (
    DEDUPE_SYSTEM_PROMPT,
    EXTRACT_SYSTEM_PROMPT,
    build_dedupe_user_prompt,
    build_extract_user_prompt,
)
from app.data.models import ChatSession, Message

logger = logging.getLogger(__name__)


@dataclass
class ReflectionResult:
    """Итог одного запуска агента."""

    facts_created: int = 0
    facts_updated: int = 0
    facts_superseded: int = 0
    candidates_total: int = 0
    candidates_skipped: int = 0  # отброшены из-за невалидной папки
    skipped_reason: str | None = None
    last_processed_message_id: str | None = None


class ReflectionAgent:
    """Агент извлечения фактов. Stateless, создаётся per-call."""

    def __init__(self, *, db: AsyncSession):
        self._db = db
        self._dossier = DossierService(db)

    async def run_for_user(self, user_id: str) -> ReflectionResult:
        """Прогнать полный цикл для одного пользователя."""
        result = ReflectionResult()

        # === Шаг 1: чекпойнт ===
        cp = await self._dossier.get_checkpoint(user_id)
        last_processed_id = cp.last_processed_message_id if cp else None

        # === Шаг 2: загрузить новые сообщения ===
        new_messages = await self._load_new_messages(user_id, last_processed_id)
        if not new_messages:
            result.skipped_reason = "no_new_messages"
            return result

        # === Шаг 3: краткое существующее досье для контекста ===
        existing = await self._dossier.get_facts_by_folders(user_id)
        existing_summary = facts_to_compact_summary(existing)

        # === Шаг 4: Extract ===
        candidates = await self._extract(new_messages, existing_summary)
        result.candidates_total = len(candidates)

        if not candidates:
            # Сдвигаем чекпойнт даже если фактов нет (чтобы не пересматривать)
            await self._dossier.update_checkpoint(
                user_id=user_id,
                last_processed_message_id=new_messages[-1].id,
                facts_extracted=0,
            )
            result.last_processed_message_id = new_messages[-1].id
            return result

        # === Шаг 5+6: Dedupe + Update ===
        session_lookup = {m.id: m.session_id for m in new_messages}

        for cand in candidates:
            folder = cand.get("candidate_folder")
            subfolder = cand.get("candidate_subfolder")
            if not is_valid_subfolder(folder, subfolder):
                logger.warning(
                    "Skipping candidate with invalid folder %s/%s: %r",
                    folder, subfolder, cand.get("summary"),
                )
                result.candidates_skipped += 1
                continue

            decision = await self._dedupe(user_id, cand)

            if (
                decision.get("decision") == "merge"
                and decision.get("target_fact_id")
            ):
                # Добавляем цитаты к существующему факту
                quotes = cand.get("quotes", [])
                for q in quotes:
                    sid = session_lookup.get(q.get("message_id"))
                    if sid is None:
                        continue
                    try:
                        await self._dossier.update_fact_with_new_quote(
                            fact_id=decision["target_fact_id"],
                            new_quote={
                                "text": q["text"],
                                "session_id": sid,
                                "message_id": q["message_id"],
                            },
                            new_severity=cand.get("severity"),
                        )
                    except ValueError:
                        # Старый факт мог быть удалён между шагами — пропустим
                        logger.warning(
                            "merge target_fact_id %s not found",
                            decision["target_fact_id"],
                        )
                result.facts_updated += 1

            elif decision.get("decision") in ("create_new", "supersede"):
                # Создаём новый факт
                quotes_input = []
                for q in cand.get("quotes", []):
                    sid = session_lookup.get(q.get("message_id"))
                    if sid is None:
                        continue
                    quotes_input.append({
                        "text": q["text"],
                        "session_id": sid,
                        "message_id": q["message_id"],
                    })

                try:
                    new_fact = await self._dossier.add_fact(
                        user_id=user_id,
                        folder=folder,
                        subfolder=subfolder,
                        summary=cand["summary"],
                        tags=cand.get("candidate_tags", []),
                        severity=cand.get("severity", 0.5),
                        confidence=cand.get("confidence", 0.5),
                        quotes=quotes_input,
                    )
                    result.facts_created += 1
                except ValueError as e:
                    logger.warning("add_fact failed: %s", e)
                    result.candidates_skipped += 1
                    continue

                if (
                    decision["decision"] == "supersede"
                    and decision.get("target_fact_id")
                ):
                    try:
                        await self._dossier.supersede_fact(
                            old_fact_id=decision["target_fact_id"],
                            new_fact_id=new_fact.id,
                        )
                        result.facts_superseded += 1
                    except ValueError:
                        pass  # старый факт уже не существует — ok
            else:
                # Невалидное решение — считаем как create_new fallback,
                # но логируем
                logger.warning(
                    "Unknown dedupe decision: %r — skipping",
                    decision,
                )
                result.candidates_skipped += 1

        # === Шаг 7: сдвинуть чекпойнт ===
        await self._dossier.update_checkpoint(
            user_id=user_id,
            last_processed_message_id=new_messages[-1].id,
            facts_extracted=result.facts_created + result.facts_updated,
        )
        result.last_processed_message_id = new_messages[-1].id

        logger.info(
            "Reflection done: user=%s created=%d updated=%d superseded=%d",
            user_id[:8],
            result.facts_created,
            result.facts_updated,
            result.facts_superseded,
        )
        return result

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------

    async def _load_new_messages(
        self,
        user_id: str,
        after_message_id: str | None,
    ) -> list[Message]:
        """Загрузить user-сообщения после чекпойнта (по всем сессиям user_id).

        Если after_message_id None — берём все user-сообщения.
        """
        # Найти server_timestamp у after_message_id (cutoff)
        cutoff_ts = None
        if after_message_id:
            cutoff_msg = await self._db.get(Message, after_message_id)
            if cutoff_msg:
                cutoff_ts = cutoff_msg.server_timestamp

        # Все сессии этого user_id
        sessions_result = await self._db.execute(
            select(ChatSession.id).where(ChatSession.user_id == user_id),
        )
        session_ids = [row[0] for row in sessions_result]
        if not session_ids:
            return []

        # User-сообщения в этих сессиях, после cutoff_ts
        stmt = (
            select(Message)
            .where(Message.session_id.in_(session_ids))
            .where(Message.role == "user")
            .order_by(Message.server_timestamp.asc())
        )
        if cutoff_ts is not None:
            stmt = stmt.where(Message.server_timestamp > cutoff_ts)

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def _extract(
        self,
        new_messages: list[Message],
        existing_summary: str,
    ) -> list[dict]:
        """Вызвать LLM extract-этапа, распарсить JSON-массив."""
        block_lines = [
            f"[message_id={m.id}] {m.content}" for m in new_messages
        ]
        block = "\n".join(block_lines)

        user_prompt = build_extract_user_prompt(
            messages_block=block,
            existing_dossier_summary=existing_summary,
        )

        provider = get_provider()
        response = await provider.generate(
            [
                LLMMessage(role="system", content=EXTRACT_SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=0.2,
            max_tokens=2000,
        )

        raw = strip_markdown_fence(response.text)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning("Reflection extract returned non-JSON: %s", e)
            return []

        if not isinstance(data, list):
            logger.warning(
                "Reflection extract returned non-list: %s",
                type(data).__name__,
            )
            return []

        return data

    async def _dedupe(self, user_id: str, candidate: dict) -> dict:
        """Решить, что делать с кандидатом: merge / create_new / supersede.

        Если в той же папке/подпапке нет фактов — сразу create_new (без LLM).
        """
        folder = candidate["candidate_folder"]
        subfolder = candidate.get("candidate_subfolder")

        # Существующие факты в этой папке
        existing = await self._dossier.get_facts_by_folders(
            user_id, folders=[folder],
        )
        # Фильтр по подпапке (если задана)
        if subfolder:
            existing = [f for f in existing if f.subfolder == subfolder]

        if not existing:
            return {"decision": "create_new", "target_fact_id": None}

        # LLM-вызов для решения
        existing_dicts = [
            {"id": f.id, "summary": f.summary, "severity": f.severity}
            for f in existing[:10]  # не больше 10 в контекст
        ]
        candidate_quotes = [
            q.get("text", "") for q in candidate.get("quotes", [])
        ]

        user_prompt = build_dedupe_user_prompt(
            candidate_summary=candidate["summary"],
            candidate_quotes=candidate_quotes,
            existing_facts=existing_dicts,
        )

        provider = get_provider()
        response = await provider.generate(
            [
                LLMMessage(role="system", content=DEDUPE_SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=0.1,
            max_tokens=300,
        )

        raw = strip_markdown_fence(response.text)

        try:
            decision = json.loads(raw)
            if decision.get("decision") not in (
                "merge", "create_new", "supersede",
            ):
                logger.warning("Bad dedupe decision: %r", decision)
                return {"decision": "create_new", "target_fact_id": None}
            return decision
        except json.JSONDecodeError:
            logger.warning("dedupe returned non-JSON, fallback to create_new")
            return {"decision": "create_new", "target_fact_id": None}
