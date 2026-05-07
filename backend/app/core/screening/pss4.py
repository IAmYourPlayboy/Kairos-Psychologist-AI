"""PSS-4 — Cohen Perceived Stress Scale (1988, 4-item version).

Валидированный опросник субъективно воспринимаемого стресса за последний
месяц. Сокращённая версия классической PSS-14/PSS-10 (Cohen, Kamarck,
Mermelstein, 1983).

Использование (в продукте):
- Предлагается пользователю не чаще раза в неделю (frequency cap).
- Влияет ТОЛЬКО на терапевтическую маршрутизацию (выбор техник CBT/DBT/ACT
  и тон бота). НЕ триггерит override risk_level — для этого есть ASQ.

ВНИМАНИЕ: формулировки ниже — точная русскоязычная адаптация.
Менять их без научной re-validation НЕЛЬЗЯ.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ============================================================================
# Типы
# ============================================================================


# 0..4 на пятибалльной шкале «никогда / почти никогда / иногда /
# довольно часто / очень часто». Для reverse-вопросов (Q2, Q3) шкала
# инвертирована в инструкции пользователю — мы инвертируем при scoring.
PSS4Answer = int  # ожидаем 0..4 включительно

PSS4Interpretation = Literal["low", "moderate", "high"]


@dataclass(frozen=True)
class PSS4Question:
    """Один вопрос опросника.

    Attributes:
        id: Порядковый номер (1..4).
        text: Текст вопроса (русский).
        reverse: True для Q2 и Q3 — у них шкала инвертируется при scoring.
                 Пользователь отвечает по той же шкале «0=никогда .. 4=очень
                 часто», но в итоговой сумме мы записываем `4 - answer`.
    """

    id: int
    text: str
    reverse: bool


# ============================================================================
# Опросник (4 вопроса)
# ============================================================================


# Точные формулировки на русском. НЕ менять без re-validation!
PSS4: list[PSS4Question] = [
    PSS4Question(
        id=1,
        text=(
            "За последний месяц как часто ты чувствовал(а), что не "
            "способен(на) контролировать важные вещи в своей жизни?"
        ),
        reverse=False,
    ),
    PSS4Question(
        id=2,
        text=(
            "За последний месяц как часто ты чувствовал(а) уверенность "
            "в способности справиться с личными проблемами?"
        ),
        reverse=True,
    ),
    PSS4Question(
        id=3,
        text=(
            "За последний месяц как часто ты чувствовал(а), что всё идёт "
            "по-твоему?"
        ),
        reverse=True,
    ),
    PSS4Question(
        id=4,
        text=(
            "За последний месяц как часто ты чувствовал(а), что трудности "
            "накапливаются настолько, что ты не можешь с ними справиться?"
        ),
        reverse=False,
    ),
]


# ============================================================================
# Результат
# ============================================================================


@dataclass
class PSS4Result:
    """Рассчитанный результат прохождения PSS-4.

    Attributes:
        interpretation: low (0–5) / moderate (6–10) / high (11–16).
        score: Сумма после коррекции reverse-вопросов (0..16).
        raw_answers: Исходный ввод (как пользователь ответил, до reverse).
    """

    interpretation: PSS4Interpretation
    score: int
    raw_answers: dict[int, int] = field(default_factory=dict)


# ============================================================================
# Скоринг
# ============================================================================


_REQUIRED_IDS: frozenset[int] = frozenset({1, 2, 3, 4})
_ANSWER_MIN: int = 0
_ANSWER_MAX: int = 4


def _interpret(score: int) -> PSS4Interpretation:
    """Свести числовой score в категорию по стандартным cut-points."""
    if score <= 5:
        return "low"
    if score <= 10:
        return "moderate"
    return "high"


def score_pss4(answers: dict[int, int]) -> PSS4Result:
    """Посчитать результат PSS-4 по ответам пользователя.

    Логика:
    - Q1, Q4: суммируем как есть.
    - Q2, Q3 (reverse): прибавляем `4 - answer`.
    - Итого 0..16, разбивается: 0–5 low / 6–10 moderate / 11–16 high.

    Args:
        answers: Словарь {question_id: answer (0..4)}. Все 4 ID обязательны.

    Returns:
        PSS4Result.

    Raises:
        ValueError: Если не хватает ответов, есть лишние id или ответ вне
                    диапазона 0..4.
    """
    # Валидация: все 4 ответа обязательны
    for qid in _REQUIRED_IDS:
        if qid not in answers:
            raise ValueError(
                f"PSS-4: missing answer for question id={qid}"
            )

    for qid, ans in answers.items():
        if qid not in _REQUIRED_IDS:
            raise ValueError(f"PSS-4: unknown question id={qid}")
        if not isinstance(ans, int):
            raise ValueError(
                f"PSS-4: answer for id={qid} must be int, got {type(ans).__name__}"
            )
        if not (_ANSWER_MIN <= ans <= _ANSWER_MAX):
            raise ValueError(
                f"PSS-4: answer for id={qid} must be 0..4, got {ans}"
            )

    # Маппинг id → reverse-флаг (один проход по списку вопросов)
    reverse_by_id: dict[int, bool] = {q.id: q.reverse for q in PSS4}

    total = 0
    for qid, ans in answers.items():
        if reverse_by_id[qid]:
            total += _ANSWER_MAX - ans
        else:
            total += ans

    return PSS4Result(
        interpretation=_interpret(total),
        score=total,
        raw_answers=dict(answers),
    )
