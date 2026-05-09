import { test, expect } from "@playwright/test";

/**
 * Soft-delete flow: register → DELETE /me → 403 на /api/chat →
 * cancel-deletion → /api/chat снова работает.
 */
test.describe("Soft delete flow", () => {
  test.beforeEach(async ({ context }) => {
    // AppShell рендерит FirstVisitModal на всех страницах.
    // Без consent-флага модалка перекрывает форму регистрации.
    await context.addInitScript(() => {
      localStorage.setItem("kairos.consent_v1_given", "1");
    });
  });

  test("DELETE /me → блокирует чат → cancel → разблокирует", async ({ page }) => {
    const uniqueEmail = `e2e-delete-${Date.now()}@example.com`;
    const password = "test-password-123";

    await page.goto("/auth/register");
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/пароль/i).first().fill(password);
    const checkboxes = page.getByRole("checkbox");
    const count = await checkboxes.count();
    for (let i = 0; i < count; i++) {
      await checkboxes.nth(i).check();
    }
    await page.getByRole("button", { name: /создать аккаунт/i }).click();
    await page.waitForURL(/\/chat/, { timeout: 10000 });

    // Идём в профиль и удаляем аккаунт
    await page.goto("/profile");
    // AccountSection рендерит «Загружаем аккаунт…» пока useAuth не дотянет пользователя.
    await expect(page.getByRole("heading", { name: "Аккаунт" })).toBeVisible({ timeout: 10000 });
    // Первая кнопка — «Удалить аккаунт» (открывает confirm Dialog)
    await page.getByRole("button", { name: /^удалить аккаунт$/i }).click();

    // Подтверждаем в Dialog — «Да, запросить удаление»
    await page.getByRole("button", { name: /да, запросить удаление/i }).click();

    // После handleDelete() делает window.location.href = "/chat" — ждём редирект.
    // Важно: auth.py:463 вызывает clear_auth_cookies(response) — после DELETE
    // пользователь уже вылогинен (cookies стёрты). Чтобы проверить блокировку
    // 403 на /api/chat — нужно сначала ЗАЛОГИНИТЬСЯ ОБРАТНО, только тогда
    // current_user != None и блокировка в chat.py:78-91 сработает.
    await page.waitForURL(/\/chat/, { timeout: 10000 });

    // Логинимся обратно — теперь deletion_scheduled_at уже проставлен в БД.
    await page.goto("/auth/login");
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/пароль/i).fill(password);
    await page.getByRole("button", { name: /^войти$/i }).click();
    await page.waitForURL(/\/chat/, { timeout: 10000 });

    // Теперь /api/chat должен вернуть 403 — pending-deletion в chat.py:78.
    const response = await page.request.post("http://localhost:3000/api/chat", {
      data: { message: "test", session_id: "11111111-1111-1111-1111-111111111111" },
    });
    expect(response.status()).toBe(403);
    // Глобальный error_handler в backend/app/middleware/error_handler.py
    // оборачивает HTTPException в { error: { type, status, message, request_id } }.
    // chat.py:78 передаёт detail как dict { code, message, scheduled_at },
    // этот dict попадает в error.message. Проверяем сериализованное тело целиком.
    const body = await response.json();
    expect(JSON.stringify(body)).toContain("account_pending_deletion");

    // Теперь идём в профиль — должен быть PendingDeletionBanner
    await page.goto("/profile");
    await expect(page.getByRole("button", { name: /отменить удаление/i })).toBeVisible({
      timeout: 10000,
    });

    // Кликаем «Отменить удаление»
    await page.getByRole("button", { name: /отменить удаление/i }).click();
    // Дать бэку обработать
    await page.waitForTimeout(1000);

    // POST /api/chat снова работает (через rewrite на 3000)
    const response2 = await page.request.post("http://localhost:3000/api/chat", {
      data: { message: "test", session_id: "22222222-2222-2222-2222-222222222222" },
    });
    expect(response2.status()).not.toBe(403);
  });
});
