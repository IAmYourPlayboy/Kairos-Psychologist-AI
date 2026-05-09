# Playwright E2E Tests

Гибрид: реальный backend (Postgres + Redis) + mock LLM.

## Запуск

В одном терминале — backend в E2E-режиме (mock LLM):

**Windows (PowerShell):**

```powershell
cd D:\Kairos\backend
$env:E2E_MODE="true"
uvicorn app.main:app --port 8001 --reload
```

**Windows (cmd):**

```cmd
cd D:\Kairos\backend
set E2E_MODE=true
uvicorn app.main:app --port 8001 --reload
```

**macOS / Linux / Git Bash:**

```bash
cd /path/to/Kairos/backend
E2E_MODE=true uvicorn app.main:app --port 8001 --reload
```

В другом терминале — Playwright:

**Windows (PowerShell / cmd):**

```powershell
cd D:\Kairos\frontend
npm run test:e2e          # headless
npm run test:e2e:ui       # с UI режимом
npm run test:e2e:debug    # пошаговая отладка
```

**macOS / Linux:**

```bash
cd /path/to/Kairos/frontend
npm run test:e2e
```

После прогона — посмотреть отчёт с падениями:

```powershell
npx playwright show-report
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
