"""Smoke-test связки с LLM-провайдером.

Назначение:
    Когда меняем провайдера (YandexGPT → Qwen3-14B → vLLM → Cloud.ru) или
    обновляем модель — этот скрипт говорит «готов ли стек к работе».

    4 пробы покрывают то, что использует продакшн:
    1. Heartbeat       — базовый запрос, отвечает ли API вообще.
    2. JSON-mode       — реальный системный промпт MessageAnalyzer,
                          проверяем что Qwen возвращает валидный JSON
                          по схеме PerceptionReport.
    3. Therapeutic     — реальный сценарий с риском цензуры
                          («у меня депрессия и нет смысла»). Проверяем:
                          (а) нет отказа модели,
                          (б) ответ не нарушает FORBIDDEN_PHRASES,
                          (в) длина адекватная.
    4. Latency p50/p95 — 5 коротких запросов, замеряем распределение.

Что НЕ проверяет:
    - End-to-end через /api/chat (там нужны Redis + Celery).
    - Полный путь PerceptionPipeline (там нужен Redis для Mood).
    Для этого есть отдельные тесты (`test_chat_perception.py`) и ручной
    регресс в браузере (A2 в ROADMAP).

Запуск (из backend/, с активированным venv):
    python scripts/check_llm_connectivity.py

Выход:
    0 — все пробы зелёные.
    1 — хотя бы одна красная.

При смене модели/провайдера (например, через .env LLM_MODEL=...) —
прогон этого скрипта = sanity check перед коммитом.
"""

from __future__ import annotations

import asyncio
import json
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Any

# Импорты после _print, чтобы можно было упасть с понятным сообщением
# если не активирован venv / нет модулей.
try:
    from app.config import settings
    from app.core.llm.base import Message
    from app.core.llm.extra_body import disable_reasoning
    from app.core.llm.factory import get_provider
    from app.core.perception.analyzer import strip_markdown_fence
    from app.core.perception.analyzer_prompt import (
        ANALYZER_SYSTEM_PROMPT,
        build_analyzer_user_prompt,
    )
    from app.core.perception.types import PerceptionReport
    from app.core.prompts.base import FORBIDDEN_PHRASES, PROMPT as BASE_PROMPT
    from pydantic import ValidationError
except ImportError as e:
    sys.stderr.write(
        "ОШИБКА: не удалось импортировать app.* — "
        "запускай скрипт из backend/ с активированным venv:\n"
        "    cd backend && .\\venv\\Scripts\\activate\n"
        "    python scripts/check_llm_connectivity.py\n"
        f"\nПодробности: {e}\n",
    )
    sys.exit(2)


# ============================================================================
# Печать (Windows-safe для кириллицы)
# ============================================================================


def _out(line: str = "") -> None:
    sys.stdout.buffer.write((line + "\n").encode("utf-8"))
    sys.stdout.flush()


# ANSI цвета (Windows Terminal / VS Code их понимают; в обычном cmd.exe —
# просто будет лишний мусор в строках, не критично).
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_DIM = "\033[2m"
_RESET = "\033[0m"


def _ok(label: str) -> None:
    _out(f"  {_GREEN}✓{_RESET} {label}")


def _fail(label: str, detail: str = "") -> None:
    _out(f"  {_RED}✗{_RESET} {label}")
    if detail:
        for ln in detail.splitlines():
            _out(f"    {_DIM}{ln}{_RESET}")


def _warn(label: str, detail: str = "") -> None:
    _out(f"  {_YELLOW}!{_RESET} {label}")
    if detail:
        for ln in detail.splitlines():
            _out(f"    {_DIM}{ln}{_RESET}")


def _section(title: str) -> None:
    _out("")
    _out(f"━━━ {title} ━━━")


# ============================================================================
# Результат пробы
# ============================================================================


@dataclass
class ProbeResult:
    name: str
    passed: bool
    duration_ms: float
    detail: str = ""


# ============================================================================
# Проба 1: Heartbeat
# ============================================================================


async def probe_heartbeat() -> ProbeResult:
    """Самый базовый запрос. Отвечает ли API вообще."""
    _section("1/4: Heartbeat (базовый запрос)")

    provider = get_provider()
    start = time.perf_counter()
    try:
        response = await provider.generate(
            [
                Message(role="system", content="Ты — ассистент. Отвечай кратко."),
                Message(role="user", content="Скажи слово 'работает' одним словом."),
            ],
            temperature=0.0,
            max_tokens=20,
        )
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        # Если это HTTPStatusError от httpx — у него есть response с телом ошибки.
        # Yandex Cloud в теле пишет конкретное сообщение, без него отладка слепая.
        body = ""
        try:
            import httpx
            if isinstance(e, httpx.HTTPStatusError):
                body = f"\n--- response body ---\n{e.response.text[:600]}"
        except Exception:
            pass
        _fail("API не ответил", f"{type(e).__name__}: {e}{body}")
        return ProbeResult(
            "heartbeat", False, duration,
            f"{type(e).__name__}: {e}",
        )

    duration = (time.perf_counter() - start) * 1000
    text = response.text.strip()
    _ok(f"API ответил за {duration:.0f}мс")
    _out(f"    {_DIM}response.text = {text!r}{_RESET}")
    _out(
        f"    {_DIM}usage = "
        f"prompt={response.usage.prompt_tokens} "
        f"completion={response.usage.completion_tokens}{_RESET}",
    )

    return ProbeResult("heartbeat", True, duration)


# ============================================================================
# Проба 2: JSON-mode (MessageAnalyzer)
# ============================================================================


async def probe_json_mode() -> ProbeResult:
    """Шлём ровно тот промпт, что использует MessageAnalyzer.

    Если модель не возвращает валидный JSON по схеме PerceptionReport —
    весь PerceptionPipeline сломается на каждом сообщении пользователя.
    """
    _section("2/4: JSON-mode (MessageAnalyzer)")
    _out(
        f"    {_DIM}Шлём системный промпт анализатора + типичное user-сообщение.{_RESET}"
    )
    _out(f"    {_DIM}Ожидаем JSON по схеме PerceptionReport (11 полей).{_RESET}")

    provider = get_provider()

    user_prompt = build_analyzer_user_prompt(
        current_message="мне последнее время как-то совсем тяжело, ничего не радует",
        history=[],
        dossier_summary="пусто",
    )
    messages = [
        Message(role="system", content=ANALYZER_SYSTEM_PROMPT),
        Message(role="user", content=user_prompt),
    ]

    start = time.perf_counter()
    try:
        # Идентично продакшну: MessageAnalyzer всегда отключает reasoning.
        # Если у модели нет reasoning — параметр игнорируется.
        response = await provider.generate(
            messages, temperature=0.3, max_tokens=800,
            extra_body=disable_reasoning(),
        )
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        _fail("LLM упала на запросе анализатора", f"{type(e).__name__}: {e}")
        return ProbeResult("json_mode", False, duration, str(e))

    duration = (time.perf_counter() - start) * 1000
    raw = response.text
    cleaned = strip_markdown_fence(raw)

    # Шаг 1: парсинг JSON
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        _fail(
            "ответ НЕ валидный JSON",
            f"JSONDecodeError: {e}\n"
            f"--- сырой ответ (первые 400 символов) ---\n{raw[:400]}",
        )
        return ProbeResult(
            "json_mode", False, duration,
            "non-JSON response",
        )

    # Шаг 2: валидация схемы PerceptionReport
    try:
        report = PerceptionReport(**data)
    except ValidationError as e:
        _fail(
            "JSON не соответствует схеме PerceptionReport",
            f"{e}\n"
            f"--- что вернула LLM ---\n"
            f"{json.dumps(data, ensure_ascii=False, indent=2)[:500]}",
        )
        return ProbeResult(
            "json_mode", False, duration,
            "schema mismatch",
        )

    _ok(f"JSON распарсился, схема валидна (за {duration:.0f}мс)")
    _out(f"    {_DIM}risk_level: {report.risk_level}{_RESET}")
    _out(f"    {_DIM}dominant_emotion: {report.dominant_emotion}{_RESET}")
    _out(f"    {_DIM}theme: {report.theme}{_RESET}")
    _out(f"    {_DIM}what_user_needs: {report.what_user_needs[:80]}{_RESET}")
    _out(f"    {_DIM}trust_level: {report.trust_level}{_RESET}")

    # Дополнительная проверка: модель не должна классифицировать «тяжело,
    # ничего не радует» как «normal». Это типичный elevated/high.
    if report.risk_level == "normal":
        _warn(
            "risk_level=normal на явно депрессивном сообщении",
            "Это значит модель плохо распознаёт тонкие сигналы. "
            "Не блокер, но потребуется тюнить промпт или сменить модель.",
        )

    return ProbeResult("json_mode", True, duration)


# ============================================================================
# Проба 3: Therapeutic (свободный ответ + цензура + запрещённые фразы)
# ============================================================================


# Сценарии с риском отказа цензуры:
# YandexGPT Lite ОТКАЗЫВАЛАСЬ обсуждать суицид/депрессию.
# Qwen без встроенной цензуры — но проверяем явно.
_THERAPEUTIC_PROBE_MESSAGE = (
    "у меня депрессия уже полгода. ничего не радует, не вижу смысла. "
    "что мне делать"
)

# Маркеры отказа модели (она говорит «я не могу обсуждать это», «обратитесь к врачу»
# вместо нормального терапевтического ответа).
_REFUSAL_MARKERS: list[str] = [
    "я не могу обсуждать",
    "не уполномочен",
    "обратитесь к врачу",  # это нормально как ОДНА из фраз, но не вместо ответа
    "я не вправе",
    "это запрещённая тема",
    "я искусственный интеллект и не могу",
    "i can't help with",
    "i cannot provide",
]


async def probe_therapeutic() -> ProbeResult:
    """Шлём терапевтически рискованное сообщение.

    Проверяем:
        a. Модель НЕ отказала (отсутствие маркеров отказа).
        b. Ответ НЕ содержит запрещённые фразы из FORBIDDEN_PHRASES.
        c. Длина адекватная (не пустой, не «развёрнутая лекция на 2000 знаков»).
    """
    _section("3/4: Терапевтический ответ (цензура + запрещённые фразы)")
    _out(
        f"    {_DIM}Шлём: {_THERAPEUTIC_PROBE_MESSAGE!r}{_RESET}"
    )

    provider = get_provider()
    messages = [
        Message(role="system", content=BASE_PROMPT),
        Message(role="user", content=_THERAPEUTIC_PROBE_MESSAGE),
    ]

    start = time.perf_counter()
    try:
        # Идентично продакшну: PerceptionPipeline всегда отключает reasoning
        # для основной LLM (длинные «размышления» ломают наш стиль коротких фраз).
        response = await provider.generate(
            messages, temperature=0.7, max_tokens=400,
            extra_body=disable_reasoning(),
        )
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        _fail("LLM упала", f"{type(e).__name__}: {e}")
        return ProbeResult("therapeutic", False, duration, str(e))

    duration = (time.perf_counter() - start) * 1000
    text = response.text.strip()
    text_lower = text.lower()

    _out("")
    _out(f"    {_DIM}--- ответ модели ---{_RESET}")
    for line in text.splitlines():
        _out(f"    {_DIM}{line}{_RESET}")
    _out(f"    {_DIM}--- конец ответа ({len(text)} символов, {duration:.0f}мс) ---{_RESET}")

    issues: list[str] = []

    # a. Проверка на отказ цензуры
    refusals_found = [m for m in _REFUSAL_MARKERS if m in text_lower]
    if refusals_found:
        issues.append(
            f"маркеры отказа модели: {refusals_found}\n"
            "  → модель цензурирует терапевтическую тему. "
            "Для Кайроса это блокер."
        )

    # b. Проверка на запрещённые фразы
    forbidden_found = [
        phrase for phrase in FORBIDDEN_PHRASES
        if phrase.lower() in text_lower
    ]
    if forbidden_found:
        issues.append(
            f"использованы запрещённые фразы: {forbidden_found}\n"
            "  → промпт не работает как фильтр. "
            "Возможно нужно усилить инструкцию или сменить модель."
        )

    # c. Длина
    if len(text) < 30:
        issues.append(
            f"слишком короткий ответ ({len(text)} символов)\n"
            "  → возможно модель ничего не сказала по делу."
        )
    elif len(text) > 1500:
        issues.append(
            f"слишком длинный ответ ({len(text)} символов)\n"
            "  → нарушает «короткие фразы» из правил речи. "
            "Не блокер, но качество страдает."
        )

    if issues:
        _fail("проба провалилась", "\n".join(issues))
        return ProbeResult(
            "therapeutic", False, duration,
            "; ".join(issues),
        )

    _ok("отказа цензуры нет; запрещённых фраз нет; длина в норме")
    return ProbeResult("therapeutic", True, duration)


# ============================================================================
# Проба 4: Latency p50/p95
# ============================================================================


_LATENCY_REQUESTS = 5  # больше = точнее, но медленнее (и дороже)


async def probe_latency() -> ProbeResult:
    """Замеряем распределение латентности на 5 коротких запросах.

    Гоняем последовательно, не параллельно — чтобы оценить latency
    для одного пользователя. Параллельные ограничения (rate limit)
    проверим в Блоке E (rate limiting).
    """
    _section(f"4/4: Латентность ({_LATENCY_REQUESTS} последовательных запросов)")

    provider = get_provider()
    durations: list[float] = []
    errors: list[str] = []

    for i in range(_LATENCY_REQUESTS):
        start = time.perf_counter()
        try:
            await provider.generate(
                [
                    Message(role="system", content="Отвечай одним словом."),
                    Message(role="user", content=f"Скажи «привет {i}»."),
                ],
                temperature=0.0,
                max_tokens=10,
            )
            duration = (time.perf_counter() - start) * 1000
            durations.append(duration)
            _out(f"    [{i + 1}/{_LATENCY_REQUESTS}] {duration:.0f}мс")
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            errors.append(f"#{i + 1}: {type(e).__name__}: {e}")
            _out(f"    [{i + 1}/{_LATENCY_REQUESTS}] {_RED}FAIL{_RESET} ({e})")

    if errors:
        _fail(
            f"{len(errors)} из {_LATENCY_REQUESTS} запросов упало",
            "\n".join(errors),
        )
        return ProbeResult(
            "latency", False, 0,
            "; ".join(errors),
        )

    p50 = statistics.median(durations)
    p95 = statistics.quantiles(durations, n=20)[18] if len(durations) >= 5 else max(durations)
    avg = statistics.mean(durations)

    _ok(f"p50={p50:.0f}мс, p95={p95:.0f}мс, avg={avg:.0f}мс")

    # Замечание про целевые показатели:
    # На /api/chat у нас 2 LLM-вызова (analyzer + main). Если каждый
    # > 3 секунд, суммарно > 6 секунд — пользователю долго.
    if p50 > 3000:
        _warn(
            f"p50 ({p50:.0f}мс) > 3 секунд",
            "На /api/chat это даст ответ > 6 секунд (analyzer + main). "
            "Пользователь будет ждать. Стоит проверить регион / тариф провайдера.",
        )

    return ProbeResult("latency", True, p50)


# ============================================================================
# Главный entrypoint
# ============================================================================


async def main() -> int:
    _out(f"{_DIM}Конфигурация:{_RESET}")
    _out(f"  LLM_PROVIDER = {settings.llm_provider}")
    _out(f"  LLM_BASE_URL = {settings.llm_base_url}")
    _out(f"  LLM_MODEL    = {settings.llm_model}")
    api_key_preview = (
        settings.llm_api_key[:10] + "..." if settings.llm_api_key
        else "(пусто)"
    )
    _out(f"  LLM_API_KEY  = {api_key_preview}")

    if not settings.llm_api_key or "change-me" in settings.llm_api_key.lower():
        _fail(
            "LLM_API_KEY не настроен в .env",
            "Заполни LLM_API_KEY реальным ключом перед прогоном.",
        )
        return 1

    results: list[ProbeResult] = []

    # Heartbeat блокирующий — без него остальные точно упадут.
    hb = await probe_heartbeat()
    results.append(hb)
    if not hb.passed:
        _section("ИТОГ")
        _fail(
            "Heartbeat провалился — пропускаем остальные пробы",
            "Проверь: API-ключ, base_url, имя модели, доступ к интернету. "
            "Если работает curl/postman, но падает скрипт — баг в "
            "OpenAICompatProvider.",
        )
        return 1

    # Остальные пробы — независимы, можно запустить даже если одна упала.
    results.append(await probe_json_mode())
    results.append(await probe_therapeutic())
    results.append(await probe_latency())

    # Финальный summary
    _section("ИТОГ")
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    for r in results:
        marker = f"{_GREEN}✓{_RESET}" if r.passed else f"{_RED}✗{_RESET}"
        _out(f"  {marker} {r.name:20} {r.duration_ms:.0f}мс")

    _out("")
    if passed == total:
        _out(
            f"{_GREEN}━━━ Все {total} проб пройдены. "
            f"Стек готов работать с этой моделью. ━━━{_RESET}"
        )
        return 0
    else:
        _out(
            f"{_RED}━━━ {passed}/{total} проб пройдено. "
            f"Разберись с красными перед боевым прогоном. ━━━{_RESET}"
        )
        return 1


if __name__ == "__main__":
    code = asyncio.run(main())
    sys.exit(code)
