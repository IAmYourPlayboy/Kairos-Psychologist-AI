"""Pydantic-модели слоя восприятия.

Эти типы — контракт между MessageAnalyzer, MoodService и PromptBuilder.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ============================================================================
# PerceptionReport — выход MessageAnalyzer
# ============================================================================


RiskLevel = Literal["normal", "elevated", "high", "immediate"]


class PerceptionReport(BaseModel):
    """Структурированный отчёт анализатора об одном сообщении пользователя.

    Дизайн: §5.3 в spec.

    Используется:
    - В MoodService.update_from_report() для расчёта новых значений 6 осей.
    - В PromptBuilder для сборки промпта основной LLM
      (folder_hints, inner_monologue, what_user_needs).
    - В data flywheel: сериализуется в messages.perception_json
      для будущего LoRA fine-tuning.
    """

    risk_level: RiskLevel = Field(
        ...,
        description="Кризисный уровень по восприятию анализатора",
    )

    dominant_emotion: str = Field(
        ..., min_length=1, max_length=50,
        description="Главная эмоция (русское слово)",
    )
    secondary_emotions: list[str] = Field(
        default_factory=list, max_length=5,
        description="До 5 второстепенных эмоций",
    )

    theme: str = Field(
        ..., min_length=1, max_length=100,
        description="Тема сообщения, slash-формат: 'family/dad-violence'",
    )

    hidden_signals: list[str] = Field(
        default_factory=list, max_length=5,
        description="Что недосказано / на что намекает пользователь",
    )

    open_questions: list[str] = Field(
        default_factory=list, max_length=5,
        description="О чём бы стоило спросить",
    )

    what_user_needs: str = Field(
        ..., min_length=1, max_length=300,
        description=(
            "Что нужно пользователю прямо сейчас "
            "(выслушать / совет / план / тишина)"
        ),
    )

    trust_level: float = Field(
        ..., ge=0.0, le=1.0,
        description=(
            "Насколько пользователь сейчас открыт "
            "(0=замкнут, 1=полная откровенность)"
        ),
    )

    folder_hints: list[str] = Field(
        default_factory=list, max_length=10,
        description=(
            "Какие папки досье подтянуть для контекста "
            "(формат: 'family/parents')"
        ),
    )

    inner_monologue: str = Field(
        ..., min_length=1, max_length=1000,
        description=(
            "Внутренние мысли Кайроса от первого лица. "
            "Только для админки/отладки. НЕ показывать пользователю."
        ),
    )


# ============================================================================
# MoodState — внутреннее состояние Кайроса в разговоре
# ============================================================================


def _label(value: float) -> str:
    """Текстовая метка для значения 0.0-1.0."""
    if value >= 0.85:
        return "максимальная"
    if value >= 0.65:
        return "высокая"
    if value >= 0.4:
        return "средняя"
    if value >= 0.2:
        return "низкая"
    return "минимальная"


class MoodState(BaseModel):
    """6 осей внутреннего состояния Кайроса.

    Дизайн: §6 в spec.

    Все оси — float [0.0, 1.0]. Хранится в Redis с ключом mood:{session_id},
    TTL 24h. Сериализация — JSON (см. model_dump_json / model_validate_json).
    """

    alertness: float = Field(0.3, ge=0.0, le=1.0)
    warmth: float = Field(0.7, ge=0.0, le=1.0)
    pace: float = Field(0.5, ge=0.0, le=1.0)
    assertiveness: float = Field(0.4, ge=0.0, le=1.0)
    trust_in_user: float = Field(0.7, ge=0.0, le=1.0)
    depth: float = Field(0.4, ge=0.0, le=1.0)

    @classmethod
    def default(cls) -> "MoodState":
        """Дефолтное состояние при первом сообщении в новой сессии."""
        return cls()

    def to_prompt_block(self) -> str:
        """Сериализовать в текстовый блок для system prompt основной LLM.

        Формат человекочитаемый: число + текстовая метка + подсказка как вести.
        Это даёт LLM согласованное поведение без overfit на конкретные значения.
        """
        return (
            "## ТЕКУЩЕЕ НАСТРОЕНИЕ (как тебе сейчас вести разговор)\n"
            f"- alertness: {self.alertness:.2f} ({_label(self.alertness)}) — "
            f"{'не пропускай сигналов риска' if self.alertness > 0.6 else 'риск умеренный'}\n"
            f"- warmth: {self.warmth:.2f} ({_label(self.warmth)}) — "
            f"{'давай больше тепла' if self.warmth > 0.7 else 'нейтральный тёплый тон'}\n"
            f"- pace: {self.pace:.2f} ({_label(self.pace)}) — "
            f"{'медленно, не торопи' if self.pace < 0.4 else 'нормальный темп'}\n"
            f"- assertiveness: {self.assertiveness:.2f} ({_label(self.assertiveness)}) — "
            f"{'не настаивай, следуй за пользователем' if self.assertiveness < 0.4 else 'можно вести'}\n"
            f"- trust_in_user: {self.trust_in_user:.2f} ({_label(self.trust_in_user)}) — "
            f"{'верь рассказу' if self.trust_in_user > 0.7 else 'уточняй детали'}\n"
            f"- depth: {self.depth:.2f} ({_label(self.depth)}) — "
            f"{'готова идти глубже' if self.depth > 0.5 else 'оставайся на поверхности'}"
        )
