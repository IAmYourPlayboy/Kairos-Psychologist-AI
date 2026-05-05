"""Сборка финального системного промпта для основной LLM.

Дизайн: §8 в spec.

Входы:
- PerceptionReport (от MessageAnalyzer)
- MoodState (текущее настроение)
- Релевантные факты досье

Выход: единая большая строка system_prompt.

Что внутри (порядок важен — последние блоки имеют наибольший вес):
1. Базовый Кайрос (роль, запреты, стиль речи) — из app.core.prompts.base
2. Кризисный блок (если risk_level != normal) — из app.core.prompts.crisis
3. Блок Mood (текстовый — текущее настроение)
4. Блок «что я знаю» (если факты есть)
5. Блок «внутренние мысли» (inner_monologue из отчёта)
6. Блок «что нужно пользователю»

Терапевтические протоколы SIX C's / WHO PFA здесь НЕ включаются явно
как раньше (через branch_a/branch_b). Кайрос имеет к ним доступ через
ссылку в base промпте, и применяет их по обстановке, опираясь на mood
и what_user_needs.
"""

from __future__ import annotations

from app.core.perception.dossier_summary import facts_to_full_dossier_block
from app.core.perception.types import MoodState, PerceptionReport
from app.core.prompts.base import PROMPT as BASE_PROMPT
from app.core.prompts.crisis import CRISIS_PROMPTS
from app.data.dossier_models import DossierFact


def build_main_prompt(
    *,
    report: PerceptionReport,
    mood: MoodState,
    relevant_facts: list[DossierFact],
) -> str:
    """Собрать системный промпт для основной LLM.

    Args:
        report: результат MessageAnalyzer.
        mood: текущее настроение Кайроса.
        relevant_facts: факты, отобранные по report.folder_hints.

    Returns:
        Полная строка system prompt.
    """
    parts: list[str] = [BASE_PROMPT]

    # Кризисный блок при не-normal риске
    crisis_block = CRISIS_PROMPTS.get(report.risk_level)
    if crisis_block:
        parts.append(crisis_block)

    # Блок настроения
    parts.append(mood.to_prompt_block())

    # Блок «что я знаю» (только если есть факты)
    dossier_block = facts_to_full_dossier_block(relevant_facts)
    if dossier_block:
        parts.append(dossier_block)

    # Блок «внутренних мыслей»
    parts.append(
        "## ТВОИ ВНУТРЕННИЕ МЫСЛИ (только для тебя, НЕ озвучивать пользователю)\n"
        f"{report.inner_monologue}"
    )

    # Блок «что нужно пользователю»
    parts.append(
        "## ЧТО НУЖНО ПОЛЬЗОВАТЕЛЮ СЕЙЧАС\n"
        f"{report.what_user_needs}"
    )

    return "\n\n".join(parts)
