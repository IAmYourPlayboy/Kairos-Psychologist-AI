import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright конфиг для e2e тестов Кайроса.
 *
 * Архитектура (ADR-2 в спеке): гибрид — реальный backend + mock LLM.
 * Backend запускается отдельно с E2E_MODE=true:
 *   `cd backend && E2E_MODE=true uvicorn app.main:app --port 8001`
 * Frontend запускается webServer'ом ниже (или используется уже запущенный
 * через reuseExistingServer).
 *
 * 3 проекта: chromium-light, chromium-dark, chromium-reduced-motion —
 * чтобы кризис-сценарий тестировался во всех режимах.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],

  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },

  projects: [
    {
      name: "chromium-light",
      use: {
        ...devices["Desktop Chrome"],
        colorScheme: "light",
      },
    },
    {
      name: "chromium-dark",
      use: {
        ...devices["Desktop Chrome"],
        colorScheme: "dark",
      },
    },
    {
      name: "chromium-reduced-motion",
      use: {
        ...devices["Desktop Chrome"],
        colorScheme: "light",
        reducedMotion: "reduce",
      },
    },
  ],

  webServer: {
    command: "npm run dev",
    port: 3000,
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
