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

    const checkboxes = page.getByRole("checkbox");
    const count = await checkboxes.count();
    for (let i = 0; i < count; i++) {
      await checkboxes.nth(i).check();
    }

    await page.getByRole("button", { name: /зарегистр/i }).click();

    await expect(page).toHaveURL(/\/chat/, { timeout: 10000 });

    await page.goto("/profile");
    await page.getByRole("button", { name: /выйти|logout/i }).first().click();
    await page.waitForURL(/\/(auth|chat)/, { timeout: 5000 });

    await page.goto("/auth/login");
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/пароль/i).fill(password);
    await page.getByRole("button", { name: /войти/i }).click();
    await expect(page).toHaveURL(/\/chat/, { timeout: 10000 });

    await page.goto("/profile");
    await page.getByRole("button", { name: /выйти везде|logout everywhere/i }).click();

    const response = await page.request.get("http://localhost:8001/api/auth/me");
    expect(response.status()).toBe(401);
  });
});
