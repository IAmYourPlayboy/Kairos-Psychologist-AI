"""Сборка финального системного промпта для основной LLM.

Дизайн:

- §8 в исходной spec слоя восприятия (Сессия 18).
- ``docs/superpowers/specs/2026-05-07-prompt-engineering-from-knowledge.md``
  (Сессия 23) — подмешивание выжимок техник по ситуации.

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
5. Подходящая техника (если подходит) — выжимка из knowledge/digests.py
6. Блок «внутренние мысли» (inner_monologue из отчёта)
7. Блок «что нужно пользователю»

В Сессии 23 (Фаза 1.3) добавлен блок 5: основная LLM теперь видит
конкретные техники SIX C's / WHO PFA / CBT / DBT / ACT, выбранные по
``theme`` и ``risk_level``. До этого протоколы были только упомянуты в
base промпте, но без содержания.
"""

from __future__ import annotations

from app.core.knowledge.digests import (
    ACT_GRIEF_DIGEST,
    CBT_ANXIETY_DIGEST,
    DBT_ANGER_DIGEST,
    PFA_GROUNDING_DIGEST,
    PFA_VALIDATION_DIGEST,
    SIX_CS_DIGEST,
)
from app.core.perception.dossier_summary import facts_to_full_dossier_block
from app.core.perception.types import MoodState, PerceptionReport
from app.core.prompts.base import PROMPT as BASE_PROMPT
from app.core.prompts.crisis import build_crisis_prompt
from app.data.dossier_models import DossierFact


# ----------------------------------------------------------------------------
# Подбор техники по ситуации (Сессия 23, Фаза 1.3).
#
# Ключевые принципы (см. spec 2026-05-07-prompt-engineering-from-knowledge.md):
# - immediate → ничего не подмешиваем (CRISIS_PROMPTS уже жёстко предписывает).
# - high → валидация перед действием.
# - elevated с эмоцией страх/паника → заземление (ВОЗ PFA).
# - тема с маркерами утраты → ACT.
# - тема с маркерами тревоги без кризиса → CBT.
# - доминирующая эмоция гнев → DBT.
# - тема с маркерами семья/конфликт/безысходность → SIX C's (мобилизация).
# - иначе → None (только база + mood + dossier, без подмешивания техник).
# ----------------------------------------------------------------------------


# Маркеры тем (ищутся подстрокой в lower(report.theme))
_GRIEF_MARKERS = ("утрат", "горе", "смерт", "потер", "ушёл", "ушел", "умер")
_ANXIETY_MARKERS = ("трев", "беспокой", "страх", "паник", "волну", "фоби")
_PANIC_MARKERS = ("паник", "удуш", "не дыш", "сердце")
_SIX_CS_MARKERS = (
    "семь", "конфликт", "ссор", "родител",
    "безысход", "тупик", "застрял",
)
_ANGER_EMOTIONS = ("гнев", "злость", "ярость", "раздраж", "бешенств")
_FEAR_EMOTIONS = ("страх", "ужас", "паник", "тревог")


def _matches_any(haystack: str, needles: tuple[str, ...]) -> bool:
    """Есть ли в `haystack` (lower-case) хотя бы одна подстрока из `needles`."""
    return any(n in haystack for n in needles)


def _pick_technique_digest(report: PerceptionReport) -> str | None:
    """Подобрать выжимку техник из knowledge/digests.py под ситуацию.

    Args:
        report: отчёт MessageAnalyzer.

    Returns:
        Текст выжимки (один из *_DIGEST), либо None если техника не подходит.

    Логика выбора (порядок важен — первое совпадение выигрывает):
    1. immediate → None (CRISIS_PROMPTS уже даёт жёсткие инструкции)
    2. high → PFA_VALIDATION_DIGEST (всегда валидация перед предложением контактов)
    3. elevated + страх/паника → PFA_GROUNDING_DIGEST (заземление)
    4. тема горя/утраты → ACT_GRIEF_DIGEST
    5. тема семьи/конфликта/безысходности → SIX_CS_DIGEST (мобилизация)
    6. эмоция гнев → DBT_ANGER_DIGEST
    7. тема тревоги без кризиса → CBT_ANXIETY_DIGEST
    8. иначе → None
    """
    # Правило 1: immediate — техники не подмешиваем (см. ADR-4 в spec).
    if report.risk_level == "immediate":
        return None

    theme_lower = report.theme.lower()
    emotion_lower = report.dominant_emotion.lower()

    # Правило 2: high — всегда валидация перед действием.
    if report.risk_level == "high":
        return PFA_VALIDATION_DIGEST

    # Правило 3: elevated + страх/паника → заземление.
    if report.risk_level == "elevated" and (
        _matches_any(emotion_lower, _FEAR_EMOTIONS)
        or _matches_any(theme_lower, _PANIC_MARKERS)
    ):
        return PFA_GROUNDING_DIGEST

    # Правило 4: утрата → ACT.
    if _matches_any(theme_lower, _GRIEF_MARKERS):
        return ACT_GRIEF_DIGEST

    # Правило 5: семья/конфликт/безысходность → SIX C's.
    if _matches_any(theme_lower, _SIX_CS_MARKERS):
        return SIX_CS_DIGEST

    # Правило 6: гнев → DBT.
    if _matches_any(emotion_lower, _ANGER_EMOTIONS):
        return DBT_ANGER_DIGEST

    # Правило 7: тревога без кризиса → CBT.
    if _matches_any(theme_lower, _ANXIETY_MARKERS):
        return CBT_ANXIETY_DIGEST

    # Правило 8: ничего не подошло.
    return None


def build_main_prompt(
    *,
    report: PerceptionReport,
    mood: MoodState,
    relevant_facts: list[DossierFact],
    age_group: str | None = None,
) -> str:
    """Собрать системный промпт для основной LLM.

    Args:
        report: результат MessageAnalyzer.
        mood: текущее настроение Кайроса.
        relevant_facts: факты, отобранные по report.folder_hints.
        age_group: "child" / "youth" / "adult" / None. Определяет какие
            кризисные контакты попадут в блок данных при risk_level != normal.
            None = показать все (консервативный дефолт).

    Returns:
        Полная строка system prompt.
    """
    parts: list[str] = [BASE_PROMPT]

    # Кризисный блок при не-normal риске (Сессия 27: переписан под принцип
    # "без хардкодных фраз" + возрастная маршрутизация телефонов через age_group).
    crisis_block = build_crisis_prompt(report.risk_level, age_group=age_group)
    if crisis_block:
        parts.append(crisis_block)

    # Блок настроения
    parts.append(mood.to_prompt_block())

    # Блок «что я знаю» (только если есть факты)
    dossier_block = facts_to_full_dossier_block(relevant_facts)
    if dossier_block:
        parts.append(dossier_block)

    # Блок «подходящая техника» (Сессия 23, Фаза 1.3).
    # Выбирается по theme + risk_level + dominant_emotion из digests.py.
    # Если ничего не подошло — блок не добавляется (минимизируем шум в промпте).
    technique_digest = _pick_technique_digest(report)
    if technique_digest:
        parts.append(technique_digest)

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
