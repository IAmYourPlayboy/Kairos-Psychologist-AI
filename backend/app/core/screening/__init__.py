"""Модуль screening — валидированные опросники Кайроса.

Поддерживаемые инструменты:
- ASQ (Ask Suicide-Screening Questions, NIH 2012) — суицидальный риск.
- PSS-4 (Cohen Perceived Stress Scale, 1988) — уровень стресса.

Архитектурные принципы (см. CLAUDE.md):
- Тексты вопросов и логика scoring живут в коде (не в БД). Менять их без
  re-validation нельзя; версия живёт в git.
- Все результаты сохраняются в общую таблицу ScreeningResult — не
  отдельные таблицы под каждый опросник.
- Положительный результат ASQ за последние 7 дней принудительно ставит
  risk_level=immediate в PerceptionPipeline. Это единственное rule-based
  исключение в post-Сессия-18 пайплайне.
"""

from app.core.screening.asq import (
    ASQ,
    ASQAnswer,
    ASQInterpretation,
    ASQQuestion,
    ASQResult,
    score_asq,
)
from app.core.screening.pss4 import (
    PSS4,
    PSS4Answer,
    PSS4Interpretation,
    PSS4Question,
    PSS4Result,
    score_pss4,
)
from app.core.screening.service import (
    ASQ_OVERRIDE_DAYS,
    OFFERED_TTL_SECONDS,
    VALID_QUESTIONNAIRES,
    ScreeningService,
    has_active_asq_positive,
)


__all__ = [
    # ASQ
    "ASQ",
    "ASQAnswer",
    "ASQInterpretation",
    "ASQQuestion",
    "ASQResult",
    "score_asq",
    # PSS-4
    "PSS4",
    "PSS4Answer",
    "PSS4Interpretation",
    "PSS4Question",
    "PSS4Result",
    "score_pss4",
    # Сервис
    "ScreeningService",
    "has_active_asq_positive",
    "ASQ_OVERRIDE_DAYS",
    "OFFERED_TTL_SECONDS",
    "VALID_QUESTIONNAIRES",
]
