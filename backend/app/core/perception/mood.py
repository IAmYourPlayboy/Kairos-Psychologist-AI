"""MoodService — Redis-обёртка над MoodState с правилами обновления.

Дизайн: §6 в spec.

Хранение:
- Ключ: mood:{session_id}
- Значение: JSON-сериализация MoodState
- TTL: 24 часа после последнего обновления

Обновление: чистые функции от PerceptionReport. Без LLM.
"""

from __future__ import annotations

import json
import logging
from typing import Protocol

from app.core.perception.types import MoodState, PerceptionReport

logger = logging.getLogger(__name__)


# Через сколько секунд протухает Mood без активности
MOOD_TTL_SECONDS = 24 * 60 * 60


class _RedisLike(Protocol):
    """Минимальный интерфейс Redis-клиента.

    Реальный — redis.asyncio.Redis. В тестах — fakeredis.aioredis.FakeRedis.
    Оба совпадают по сигнатурам этих методов.
    """

    async def get(self, key: str) -> bytes | None: ...
    async def set(self, key: str, value: str, ex: int | None = None) -> bool: ...
    async def delete(self, *keys: str) -> int: ...


def _key(session_id: str) -> str:
    return f"mood:{session_id}"


# ============================================================================
# Формулы обновления (чистые функции)
# ============================================================================


def _risk_to_alertness(risk: str) -> float:
    """Целевая alertness для уровня риска."""
    return {
        "normal": 0.2,
        "elevated": 0.55,
        "high": 0.85,
        "immediate": 0.98,
    }.get(risk, 0.3)


def _risk_to_pace(risk: str) -> float:
    """При высоком риске темп замедляется (короткие фразы, паузы)."""
    return {
        "normal": 0.5,
        "elevated": 0.4,
        "high": 0.25,
        "immediate": 0.15,
    }.get(risk, 0.5)


def _risk_to_warmth_floor(risk: str) -> float:
    """Минимальная warmth при данном риске.

    При высоком риске нужно БОЛЬШЕ тепла, не меньше — потому что
    человеку плохо, ему нужна поддержка, а не клинический тон.
    """
    return {
        "normal": 0.55,
        "elevated": 0.7,
        "high": 0.85,
        "immediate": 0.95,
    }.get(risk, 0.6)


# ============================================================================
# Категоризация эмоций для коррекции warmth
# ============================================================================
# Расширяемый словарь корней → семантическая категория. Добавил новый корень
# в существующую категорию — формула обновилась автоматически без правок
# логики. Корни ищутся подстрокой (lower-case), поэтому покрывают разные
# словоформы: "страх" ловит "страшно", "испугался"; "уны" — "уныние", "унылый".
EMOTION_CATEGORIES: dict[str, tuple[str, ...]] = {
    # Уязвимые / печальные / беспомощные — нужен максимум тепла
    "vulnerable": (
        "страх", "испуг", "ужас",
        "горе", "утрата", "печаль", "грусть", "тоска",
        "одиноч", "оставлен", "брошен",
        "беспомощ", "бесполезн", "никчёмн", "никчемн",
        "отчаян", "безнадёж", "безнадеж", "уны", "истощ",
        "обида", "стыд", "вина",
        "тревог", "паник", "беспокойств", "напряжён", "напряжен",
    ),
    # Гневные / агрессивные — НЕ зеркалить агрессию, чуть-чуть снизить тепло
    "angry": (
        "злост", "злоб", "гнев", "ярост", "бешен",
        "ненавист", "раздражен", "раздражён", "досад",
    ),
    # Радостные / нейтральные — без коррекции
    # (radost / spokoin... покрываются дефолтом 0.0)
}

# Коэффициенты warmth-дельты по категории.
EMOTION_WARMTH_DELTA: dict[str, float] = {
    "vulnerable": +0.1,
    "angry": -0.05,
}


def _classify_emotion(emotion: str) -> str | None:
    """Определить категорию эмоции по корням.

    Returns:
        Имя категории из EMOTION_CATEGORIES или None если не подошла ни одна.
    """
    if not emotion:
        return None
    e = emotion.lower()
    for category, roots in EMOTION_CATEGORIES.items():
        if any(root in e for root in roots):
            return category
    return None


def _emotion_warmth_delta(emotion: str) -> float:
    """Эмоция даёт небольшую коррекцию warmth.

    Уязвимые/печальные эмоции → больше тепла (+0.1).
    Гневные → чуть меньше тепла (-0.05), но не холодно (не зеркалить агрессию).
    Незнакомые/нейтральные → 0.0.
    """
    category = _classify_emotion(emotion)
    if category is None:
        return 0.0
    return EMOTION_WARMTH_DELTA.get(category, 0.0)


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def compute_next_mood(prev: MoodState, report: PerceptionReport) -> MoodState:
    """Рассчитать новое состояние Mood по предыдущему + отчёту.

    Чистая функция, без I/O — удобно тестировать и предсказывать поведение.

    Логика:
    - alertness реагирует БЫСТРО (растёт сразу к target), затухает плавно (×0.7).
    - warmth подталкивается полом по риску + эмоция-коррекция.
    - pace целиком определяется риском (детерминирован).
    - assertiveness следует за trust, кроме immediate (там низкая всегда).
    - trust_in_user сглаживается: 50% старого + 50% нового.
    - depth: при high/immediate низкая (стабилизация), иначе следует за trust.
    """
    target_alertness = _risk_to_alertness(report.risk_level)
    if target_alertness > prev.alertness:
        # Эскалация — реагируем сразу
        new_alertness = target_alertness
    else:
        # Деэскалация — затухаем плавно, но не ниже target
        new_alertness = max(prev.alertness * 0.7, target_alertness)

    target_warmth_floor = _risk_to_warmth_floor(report.risk_level)
    new_warmth = _clamp(
        max(
            prev.warmth + _emotion_warmth_delta(report.dominant_emotion),
            target_warmth_floor,
        ),
        lo=0.3, hi=1.0,
    )

    new_pace = _risk_to_pace(report.risk_level)

    # Assertiveness — следует за trust (если пользователь открыт, можно вести),
    # но при immediate всегда низкая (не давить).
    if report.risk_level == "immediate":
        new_assertiveness = 0.2
    else:
        new_assertiveness = _clamp(0.3 + 0.4 * report.trust_level)

    # Trust_in_user — сглаживаем
    new_trust = _clamp(0.5 * prev.trust_in_user + 0.5 * report.trust_level)

    # Depth — высокий trust + низкий риск = можно глубже
    if report.risk_level in ("high", "immediate"):
        new_depth = 0.4  # фокус на стабилизации, не на глубине
    else:
        new_depth = _clamp(0.3 + 0.6 * report.trust_level)

    return MoodState(
        alertness=new_alertness,
        warmth=new_warmth,
        pace=new_pace,
        assertiveness=new_assertiveness,
        trust_in_user=new_trust,
        depth=new_depth,
    )


# ============================================================================
# Сервис (Redis-обёртка)
# ============================================================================


class MoodService:
    """Сервис над Redis для хранения/обновления MoodState.

    Принимает Redis-клиент в конструктор — это упрощает тесты (fakeredis).
    """

    def __init__(self, redis_client: _RedisLike):
        self._redis = redis_client

    async def get(self, session_id: str) -> MoodState:
        """Получить текущее настроение или дефолт, если ключа нет."""
        raw = await self._redis.get(_key(session_id))
        if raw is None:
            return MoodState.default()
        try:
            data = json.loads(raw)
            return MoodState(**data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(
                "Corrupted mood state for session=%s: %s. Returning default.",
                session_id, e,
            )
            return MoodState.default()

    async def set(self, session_id: str, mood: MoodState) -> None:
        """Сохранить настроение с TTL."""
        await self._redis.set(
            _key(session_id),
            mood.model_dump_json(),
            ex=MOOD_TTL_SECONDS,
        )

    async def update_from_report(
        self,
        session_id: str,
        report: PerceptionReport,
    ) -> MoodState:
        """Прочитать текущее, применить правила, сохранить, вернуть новое."""
        prev = await self.get(session_id)
        new = compute_next_mood(prev, report)
        await self.set(session_id, new)
        return new

    async def clear(self, session_id: str) -> None:
        """Удалить состояние сессии (для тестов / выхода пользователя)."""
        await self._redis.delete(_key(session_id))
