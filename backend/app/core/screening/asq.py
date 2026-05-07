"""ASQ — Ask Suicide-Screening Questions (NIH 2012).

Валидированный 4-вопросный скринер суицидального риска от
National Institute of Mental Health (NIMH) + 5-й вопрос на acuity
(острая угроза прямо сейчас).

Использование (в продукте):
- Предлагается пользователю в первой сессии или при обнаружении
  устойчивых маркеров безысходности/изоляции.
- Если screen positive (любой "yes" на 1–4) → дополнительно задаётся
  5-й вопрос про мысли «прямо сейчас».
- Положительный результат (non_acute_positive / acute_positive) на
  ближайшие 7 дней принудительно повышает risk_level до "immediate"
  во всех вызовах /api/chat (см. ScreeningService.get_active_asq_positive).
  Это **единственное** rule-based исключение в post-Сессия-18 пайплайне:
  ASQ — валидированный научный инструмент, поэтому override допустим.

ВНИМАНИЕ: формулировки ниже — точная русскоязычная адаптация ASQ.
Менять их без научной re-validation НЕЛЬЗЯ.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ============================================================================
# Типы
# ============================================================================


# Допустимые ответы. "decline" = пользователь отказался отвечать
# (трактуем как "no" для скоринга, но логируем отдельно).
ASQAnswer = Literal["yes", "no", "decline"]

ASQInterpretation = Literal[
    "negative",            # все ответы 1–4 = "no" (или "decline")
    "non_acute_positive",  # есть "yes" на 1–4, но "нет" на 5-й (acuity)
    "acute_positive",      # есть "yes" на 1–4 и "yes" на 5-й (острая угроза)
]


@dataclass(frozen=True)
class ASQQuestion:
    """Один вопрос опросника.

    Attributes:
        id: Порядковый номер (1..5).
        text: Текст вопроса (русский, валидированная формулировка).
        is_acuity: True для 5-го вопроса (острая угроза «прямо сейчас»).
                   Этот вопрос задаётся только если на 1–4 был хотя бы один "yes".
    """

    id: int
    text: str
    is_acuity: bool


# ============================================================================
# Опросник (4 основных + 1 acuity)
# ============================================================================


# Точные формулировки на русском. НЕ менять без научной re-validation!
ASQ: list[ASQQuestion] = [
    ASQQuestion(
        id=1,
        text=(
            "За последние недели тебе хотелось не быть живым(ой)?"
        ),
        is_acuity=False,
    ),
    ASQQuestion(
        id=2,
        text=(
            "За последние недели ты думал(а), что твоей семье или друзьям "
            "было бы лучше, если бы тебя не стало?"
        ),
        is_acuity=False,
    ),
    ASQQuestion(
        id=3,
        text=(
            "За последнюю неделю у тебя были мысли о самоубийстве?"
        ),
        is_acuity=False,
    ),
    ASQQuestion(
        id=4,
        text=(
            "Ты когда-либо пытался(ась) причинить себе вред с целью "
            "покончить с жизнью?"
        ),
        is_acuity=False,
    ),
    # 5-й — задаётся ТОЛЬКО если на 1–4 был хотя бы один "yes"
    ASQQuestion(
        id=5,
        text=(
            "Прямо сейчас у тебя есть мысли о самоубийстве?"
        ),
        is_acuity=True,
    ),
]


# ============================================================================
# Результат
# ============================================================================


@dataclass
class ASQResult:
    """Рассчитанный результат прохождения ASQ.

    Attributes:
        interpretation: Категория результата (negative / non_acute_positive /
                        acute_positive).
        score: Числовой код для БД (0 = negative, 1 = non_acute_positive,
               2 = acute_positive). Полезно для агрегаций/отчётов.
        is_positive: True если interpretation in {non_acute, acute} positive.
                     Именно по этому флагу триггерится override risk_level.
        raw_answers: Исходный ввод (для аудита и сохранения в БД).
    """

    interpretation: ASQInterpretation
    score: int
    is_positive: bool
    raw_answers: dict[int, ASQAnswer] = field(default_factory=dict)


# ============================================================================
# Скоринг
# ============================================================================


# Множества id вопросов (для удобства проверок)
_CORE_IDS: frozenset[int] = frozenset({1, 2, 3, 4})
_ACUITY_ID: int = 5


def _is_yes(answer: ASQAnswer | None) -> bool:
    """Считаем "yes"; "no" / "decline" / отсутствие — не позитив."""
    return answer == "yes"


def score_asq(answers: dict[int, ASQAnswer]) -> ASQResult:
    """Посчитать результат ASQ по ответам пользователя.

    Логика:
    - Все ответы 1–4 = "no"/"decline" → `negative`.
    - Хотя бы один "yes" в 1–4 + 5-й "no"/"decline"/отсутствует → `non_acute_positive`.
    - Хотя бы один "yes" в 1–4 + 5-й "yes" → `acute_positive`.

    Args:
        answers: Словарь {question_id: answer}. Должен содержать как минимум
                 ответы на вопросы 1..4 (если 5-го yes нет среди 1–4 — он
                 не нужен; иначе ожидаем и его).

    Returns:
        ASQResult с интерпретацией и score (0/1/2).

    Raises:
        ValueError: Если отсутствуют ответы на core-вопросы (1..4) или
                    встретились неизвестные id, или передан недопустимый ответ.
    """
    # Валидация структуры
    for qid in _CORE_IDS:
        if qid not in answers:
            raise ValueError(
                f"ASQ: missing answer for core question id={qid}"
            )

    valid_answers: tuple[str, ...] = ("yes", "no", "decline")
    for qid, ans in answers.items():
        if qid not in {*_CORE_IDS, _ACUITY_ID}:
            raise ValueError(f"ASQ: unknown question id={qid}")
        if ans not in valid_answers:
            raise ValueError(
                f"ASQ: invalid answer '{ans}' for question id={qid}"
            )

    # Проверка core-вопросов (1..4)
    has_core_yes = any(_is_yes(answers.get(qid)) for qid in _CORE_IDS)

    # 5-й (acuity) учитываем ТОЛЬКО если есть core_yes
    acuity_answer: ASQAnswer | None = answers.get(_ACUITY_ID)

    if not has_core_yes:
        return ASQResult(
            interpretation="negative",
            score=0,
            is_positive=False,
            raw_answers=dict(answers),
        )

    if _is_yes(acuity_answer):
        return ASQResult(
            interpretation="acute_positive",
            score=2,
            is_positive=True,
            raw_answers=dict(answers),
        )

    return ASQResult(
        interpretation="non_acute_positive",
        score=1,
        is_positive=True,
        raw_answers=dict(answers),
    )
