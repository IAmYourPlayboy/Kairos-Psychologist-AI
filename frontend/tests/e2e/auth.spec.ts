import { test, expect } from "@playwright/test";

/**
 * Auth flow: register → logout → login → logout-everywhere.
 *
 * Использует уникальные email с timestamp чтобы тест мог идти повторно
 * без чистки БД.
 */
test.describe("Auth flow", () => {
  test("register → logout → login → logout-everywhere", async ({ page }) => {
    const uniqueEmail = `e2e-test-${Date.now()}@example.com`;
    const password = "test-password-123";

    await page.goto("/auth/register");
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/пароль/i).first().fill(password);

    // Принять чекбоксы согласий (если есть на странице — для нового guest_id)
    const checkboxes = page.getByRole("checkbox");
    const count = await checkboxes.count();
    for (let i = 0; i < count; i++) {
      await checkboxes.nth(i).check();
    }

    // Реальный текст кнопки: «Создать аккаунт»
    await page.getByRole("button", { name: /создать аккаунт/i }).click();

    // После регистрации редирект на /chat
    await expect(page).toHaveURL(/\/chat/, { timeout: 10000 });

    // Logout через профиль (кнопка «Выйти» — первая, «Выйти со всех устройств» — вторая)
    await page.goto("/profile");
    await page.getByRole("button", { name: /^выйти$/i }).click();
    await page.waitForURL(/\/(auth|chat|$)/, { timeout: 5000 });

    // Login обратно
    await page.goto("/auth/login");
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/пароль/i).fill(password);
    await page.getByRole("button", { name: /^войти$/i }).click();
    await expect(page).toHaveURL(/\/chat/, { timeout: 10000 });

    // Logout everywhere
    await page.goto("/profile");
    await page.getByRole("button", { name: /выйти со всех устройств/i }).click();

    // Проверяем что cookies очищены (через GET /api/auth/me)
    await page.waitForTimeout(500); // дать бэку обработать
    const response = await page.request.get("http://localhost:8001/api/auth/me");
    expect(response.status()).toBe(401);
  });
});
