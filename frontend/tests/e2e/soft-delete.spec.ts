import { test, expect } from "@playwright/test";

/**
 * Soft-delete flow: register → DELETE /me → 403 на /api/chat →
 * cancel-deletion → /api/chat снова работает.
 */
test.describe("Soft delete flow", () => {
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
    // Первая кнопка — «Удалить аккаунт» (открывает confirm Dialog)
    await page.getByRole("button", { name: /^удалить аккаунт$/i }).click();

    // Подтверждаем в Dialog — «Да, запросить удаление»
    await page.getByRole("button", { name: /да, запросить удаление/i }).click();

    // Дать бэку пометить удаление
    await page.waitForTimeout(500);

    // POST /api/chat должен вернуть 403
    const response = await page.request.post("http://localhost:8001/api/chat", {
      data: { message: "test", session_id: "11111111-1111-1111-1111-111111111111" },
    });
    expect(response.status()).toBe(403);
    const body = await response.json();
    expect(body.detail).toContain("account_pending_deletion");

    // Возвращаемся в профиль и отменяем удаление
    await page.goto("/profile");

    // Должен быть PendingDeletionBanner с текстом про «удаление»
    await expect(page.getByText(/удаление/i).first()).toBeVisible();

    // Кликаем «Отменить удаление»
    await page.getByRole("button", { name: /отменить удаление/i }).click();

    // POST /api/chat снова работает
    await page.waitForTimeout(1000);
    const response2 = await page.request.post("http://localhost:8001/api/chat", {
      data: { message: "test", session_id: "22222222-2222-2222-2222-222222222222" },
    });
    expect(response2.status()).not.toBe(403);
  });
});
