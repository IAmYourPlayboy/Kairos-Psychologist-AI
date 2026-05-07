"""Экспорт обезличенного датасета для исследований и LoRA fine-tuning.

Цель: выгрузить диалоги в формате JSONL, пригодном для:
1. LoRA fine-tuning основной модели на собственных данных
2. Академических публикаций по протоколу `docs/research/research_protocol.md`
3. A/B тестирования промптов

Что делает экспортёр:
1. Берёт все сессии (или фильтр по дате/outcome) из БД.
2. Для каждой сессии собирает messages в правильном порядке.
3. Применяет K-анонимность (k≥5) — удаляет уникальные комбинации квазиидентификаторов.
4. Складывает в JSONL: одна строка = одна сессия.

Что НЕ делает:
- Не анонимизирует тексты повторно — они уже анонимизированы при записи (Блок B1).
- Не выгружает оригиналы ПДн — их нет в БД.
- Не выгружает feedback от других пользователей — только агрегаты.

Формат строки JSONL:
{
    "session_id": "...",          # анонимный UUID, не привязан к user_id
    "duration_seconds": 1234,
    "message_count": 12,
    "crisis_level_max": "elevated",
    "outcome": "improved",
    "self_report_before": 3,
    "self_report_after": 6,
    "messages": [
        {
            "role": "user",
            "content": "анонимизированный текст",
            "crisis_level": "normal",
            "perception": {                  # из perception_json
                "risk_level": "...",
                "dominant_emotion": "...",
                "theme": "...",
                ...
            }
        },
        ...
    ],
    "feedback": [                            # агрегат, без таймстемпов
        {"event_type": "thumbs_up", "message_index": 3},
        ...
    ]
}

K-анонимность (k≥5):
    Квазиидентификаторы (QI) — комбинация:
    - crisis_level_max
    - outcome
    - длина сессии (бакеты: <2мин, 2-10мин, 10-30мин, >30мин)

    Если в датасете <5 сессий с одинаковой комбинацией QI — записи отбрасываются
    (или комбинация обобщается). Это защита от ре-идентификации через косвенные
    признаки.

CLI:
    python -m app.data.research_export \\
        --since 2026-01-01 \\
        --output dataset.jsonl \\
        --k 5
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.data.database import async_session_factory
from app.data.models import ChatSession, FeedbackEvent, Message

logger = logging.getLogger(__name__)


# ============================================================================
# Бакетизация длительности (для K-анонимности)
# ============================================================================


def bucket_duration(seconds: int | None) -> str:
    """Бакет длительности сессии для K-анонимности.

    Грубая категоризация — чтобы похожие сессии не были уникальными по точному
    значению (1234 секунды — уникум; «2-10 минут» — общий бакет).
    """
    if seconds is None:
        return "unknown"
    if seconds < 120:
        return "<2min"
    if seconds < 600:
        return "2-10min"
    if seconds < 1800:
        return "10-30min"
    return ">30min"


# ============================================================================
# Структура экспортируемой сессии
# ============================================================================


@dataclass
class ExportedSession:
    """Сессия в формате для экспорта (внутренний DTO)."""

    session_id: str
    duration_seconds: int | None
    message_count: int
    crisis_level_max: str
    outcome: str | None
    self_report_before: int | None
    self_report_after: int | None
    messages: list[dict[str, Any]] = field(default_factory=list)
    feedback: list[dict[str, Any]] = field(default_factory=list)

    def quasi_identifier(self) -> tuple[str, str, str]:
        """Кортеж квазиидентификаторов для K-анонимности."""
        return (
            self.crisis_level_max,
            self.outcome or "none",
            bucket_duration(self.duration_seconds),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "duration_seconds": self.duration_seconds,
            "message_count": self.message_count,
            "crisis_level_max": self.crisis_level_max,
            "outcome": self.outcome,
            "self_report_before": self.self_report_before,
            "self_report_after": self.self_report_after,
            "messages": self.messages,
            "feedback": self.feedback,
        }


# ============================================================================
# Загрузка из БД
# ============================================================================


async def load_sessions(
    db: AsyncSession,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    only_with_feedback: bool = False,
) -> list[ExportedSession]:
    """Загрузить сессии из БД и преобразовать в ExportedSession.

    Args:
        since: только сессии созданные после этой даты
        until: только сессии до этой даты
        only_with_feedback: только сессии с хотя бы одним feedback_event
    """
    stmt = select(ChatSession).options(
        selectinload(ChatSession.messages),
        selectinload(ChatSession.feedback_events),
    )
    if since is not None:
        stmt = stmt.where(ChatSession.created_at >= since)
    if until is not None:
        stmt = stmt.where(ChatSession.created_at <= until)

    result = await db.execute(stmt)
    sessions = result.scalars().unique().all()

    exported: list[ExportedSession] = []
    for s in sessions:
        if only_with_feedback and not s.feedback_events:
            continue

        exp = ExportedSession(
            session_id=s.id,
            duration_seconds=s.duration_seconds,
            message_count=s.message_count,
            crisis_level_max=s.crisis_level_max,
            outcome=s.outcome,
            self_report_before=s.self_report_before,
            self_report_after=s.self_report_after,
        )

        # Сообщения уже анонимизированы при записи (Блок B1).
        # Просто переносим их в формат для экспорта.
        for m in sorted(s.messages, key=lambda x: x.server_timestamp):
            msg_dict: dict[str, Any] = {
                "role": m.role,
                "content": m.content,
                "crisis_level": m.crisis_level,
            }
            if m.perception_json:
                try:
                    msg_dict["perception"] = json.loads(m.perception_json)
                except (json.JSONDecodeError, TypeError):
                    msg_dict["perception"] = None
            exp.messages.append(msg_dict)

        # Feedback — без таймстемпов, только тип события.
        # Привязка к конкретному message_id могла бы быть полезна,
        # но в exported.messages мы не сохраняем id (это лишняя ПДн-связка).
        # Поэтому feedback здесь — простой агрегат.
        for fb in s.feedback_events:
            exp.feedback.append({"event_type": fb.event_type})

        exported.append(exp)

    return exported


# ============================================================================
# K-анонимность
# ============================================================================


@dataclass
class KAnonymityReport:
    """Отчёт о применении K-анонимности."""

    total_in: int
    total_out: int
    dropped_count: int
    dropped_by_qi: dict[str, int] = field(default_factory=dict)
    k: int = 5

    @property
    def passed(self) -> bool:
        return self.total_out > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "k": self.k,
            "total_in": self.total_in,
            "total_out": self.total_out,
            "dropped_count": self.dropped_count,
            "dropped_by_qi": self.dropped_by_qi,
        }


def apply_k_anonymity(
    sessions: list[ExportedSession], k: int = 5
) -> tuple[list[ExportedSession], KAnonymityReport]:
    """Применить K-анонимность (k≥k).

    Удаляет сессии, у которых комбинация квазиидентификаторов встречается
    в датасете <k раз. Это защита от ре-идентификации.

    Args:
        sessions: список сессий
        k: минимальный размер класса эквивалентности (по умолчанию 5)

    Returns:
        (отфильтрованные_сессии, отчёт)
    """
    counter: Counter[tuple[str, str, str]] = Counter()
    for s in sessions:
        counter[s.quasi_identifier()] += 1

    kept: list[ExportedSession] = []
    dropped_by_qi: dict[str, int] = {}
    for s in sessions:
        qi = s.quasi_identifier()
        if counter[qi] >= k:
            kept.append(s)
        else:
            qi_key = "|".join(qi)
            dropped_by_qi[qi_key] = dropped_by_qi.get(qi_key, 0) + 1

    report = KAnonymityReport(
        total_in=len(sessions),
        total_out=len(kept),
        dropped_count=len(sessions) - len(kept),
        dropped_by_qi=dropped_by_qi,
        k=k,
    )
    return kept, report


# ============================================================================
# Запись в JSONL
# ============================================================================


def write_jsonl(sessions: list[ExportedSession], output: Path) -> int:
    """Записать сессии в JSONL-файл.

    Returns:
        Количество записанных строк.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8") as f:
        for s in sessions:
            f.write(json.dumps(s.to_dict(), ensure_ascii=False) + "\n")
            count += 1
    return count


# ============================================================================
# Главная функция экспорта
# ============================================================================


async def export_dataset(
    *,
    output: Path,
    since: datetime | None = None,
    until: datetime | None = None,
    only_with_feedback: bool = False,
    k: int = 5,
) -> dict[str, Any]:
    """Полный цикл экспорта: загрузка → K-анонимность → запись.

    Returns:
        dict с метаданными: количество, k-anonymity отчёт, путь к файлу.
    """
    async with async_session_factory() as db:
        sessions = await load_sessions(
            db,
            since=since,
            until=until,
            only_with_feedback=only_with_feedback,
        )

    logger.info("Loaded %d sessions from DB", len(sessions))

    kept, k_report = apply_k_anonymity(sessions, k=k)
    logger.info(
        "K-anonymity (k=%d): kept %d / %d sessions",
        k, len(kept), len(sessions),
    )

    written = write_jsonl(kept, output)
    logger.info("Written %d sessions to %s", written, output)

    return {
        "output": str(output),
        "written": written,
        "k_anonymity": k_report.to_dict(),
        "filters": {
            "since": since.isoformat() if since else None,
            "until": until.isoformat() if until else None,
            "only_with_feedback": only_with_feedback,
        },
    }


# ============================================================================
# CLI
# ============================================================================


def _parse_date(s: str) -> datetime:
    """Парсинг даты в ISO-формате (YYYY-MM-DD) с UTC-таймзоной."""
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def main() -> None:
    """CLI-вход.

    Пример:
        python -m app.data.research_export \\
            --since 2026-01-01 \\
            --output exports/dataset_2026.jsonl \\
            --k 5
    """
    parser = argparse.ArgumentParser(
        description="Экспорт обезличенного датасета для LoRA / исследований",
    )
    parser.add_argument(
        "--output", type=Path, required=True,
        help="Путь к JSONL-файлу для записи",
    )
    parser.add_argument(
        "--since", type=_parse_date, default=None,
        help="Только сессии с этой даты (ISO: YYYY-MM-DD)",
    )
    parser.add_argument(
        "--until", type=_parse_date, default=None,
        help="Только сессии до этой даты (ISO: YYYY-MM-DD)",
    )
    parser.add_argument(
        "--only-with-feedback", action="store_true",
        help="Только сессии с хотя бы одним feedback_event",
    )
    parser.add_argument(
        "--k", type=int, default=5,
        help="Параметр K-анонимности (по умолчанию 5)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Подробный вывод",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    result = asyncio.run(export_dataset(
        output=args.output,
        since=args.since,
        until=args.until,
        only_with_feedback=args.only_with_feedback,
        k=args.k,
    ))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
