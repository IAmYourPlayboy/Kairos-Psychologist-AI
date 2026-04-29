> **Версия**: 3.0 (Оптимизированная) | **Дата**: Апрель 2026
> **Объединяет**: CLAUDE.md v2.1 + AI_PSYCHOLOGIST_DEVELOPMENT_PLAN_v1 + PROJECT_KNOWLEDGE_BASE v3/v4 + исследование инфраструктуры
> **Как пользоваться**: открой Claude Code, прикрепи этот файл и говори «делай блок X». Каждый блок самодостаточен.

---

# ФИЛОСОФИЯ ПРОЕКТА

**Три принципа разработки:**

1. **Data Flywheel с первого дня** — каждый пользователь делает продукт лучше для следующего. Архитектура заточена под сбор обучающих сигналов в фундаменте, не «потом прикрутим». Через 500+ диалогов — LoRA fine-tuning. Русскоязычных терапевтических данных с размеченными outcomes не существует ни у кого. Это главное конкурентное преимущество.

2. **Абстракция везде** — LLM-провайдер, NLP-пайплайн, хранилище за интерфейсами. Замена компонента = смена одного класса, не переписывание всего. OpenAI-совместимый клиент работает с локальным vLLM, Yandex Cloud AI Studio, Cloud.ru — переключение = одна переменная окружения.

3. **Фундамент, а не фасад** — правильная структура БД, логирование, пайплайн данных. UI простой, данные идеальные. Тратим время на правильную структуру БД, логирование, пайплайн данных.

**Ключевой инсайт инфраструктуры**: не нужен GPU-сервер для MVP. Inference-as-a-service (Yandex Cloud AI Studio: Qwen3-14B за 0.40₽/1K токенов, Cloud.ru бесплатно) радикально снижает порог входа. Бюджет MVP: **~2 000-3 000₽/мес** вместо 10 000₽.

**Стратегия LLM**:
- **MVP (Месяц 1-4)**: Yandex Cloud AI Studio API (Qwen3-14B, 0.40₽/1K токенов) или Cloud.ru (бесплатно)
- **Рост (Месяц 5+)**: self-hosted vLLM на арендованном GPU (с грантом) или продолжить API
- **Абстракция**: один и тот же код работает с любым OpenAI-совместимым API

---

# BEHAVIORAL GUIDELINES

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

Tradeoff: These guidelines bias toward caution over speed. For trivial tasks, use judgment.

1. Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

2. Simplicity First

Minimum code that solves the problem. Nothing speculative.
- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

3. Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
