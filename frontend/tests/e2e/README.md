# Playwright E2E Tests

Гибрид: реальный backend (Postgres + Redis) + mock LLM.

## Запуск

В одном терминале:

```bash
cd backend
E2E_MODE=true uvicorn app.main:app --port 8001 --reload
```

В другом терминале:

```bash
cd frontend
npm run test:e2e          # headless
npm run test:e2e:ui       # с UI режимом
npm run test:e2e:debug    # пошаговая отладка
```

## Проекты

- `chromium-light` — основной режим
- `chromium-dark` — тёмная тема
- `chromium-reduced-motion` — `prefers-reduced-motion: reduce`

Запустить только один проект:

```bash
npm run test:e2e -- --project=chromium-light
```

## Mock LLM

При `E2E_MODE=true` backend возвращает `MockLLMProvider` —
детерминистичные ответы по ключевым словам:
- «хочу умереть» → `risk_level: immediate`
- «страшно, не могу заснуть» → `risk_level: elevated`
- «бессмысленно, нет выхода» → `risk_level: high`
- иначе → `normal`

См. `backend/app/core/llm/mock.py`.

## Что НЕ покрыто

- Реальные ответы LLM (это вручную в Фазе 1)
- Платежи (только mock-flow)
- Real-time подписки
