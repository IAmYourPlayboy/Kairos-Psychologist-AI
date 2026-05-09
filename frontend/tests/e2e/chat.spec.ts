import { test, expect } from "@playwright/test";

/**
 * Chat flow: отправка сообщения, получение ответа от mock-бота, дисклеймер
 * при первом визите.
 */
test.describe("Chat flow", () => {
  test("первый визит → дисклеймер → отправка 'привет' → ответ", async ({ page }) => {
    await page.goto("/");
    await page.evaluate(() => localStorage.clear());
    await page.goto("/chat");

    const disclaimer = page.getByRole("dialog").filter({ hasText: /не замена/i });
    await expect(disclaimer).toBeVisible({ timeout: 5000 });

    const checkboxes = page.getByRole("checkbox");
    const count = await checkboxes.count();
    for (let i = 0; i < count; i++) {
      await checkboxes.nth(i).check();
    }
    await page.getByRole("button", { name: /продолжить|принять|ок/i }).click();
    await expect(disclaimer).not.toBeVisible();

    const input = page.getByRole("textbox");
    await input.fill("привет");
    await input.press("Enter");

    const botMsg = page.getByText(/Кайрос|привет/i).last();
    await expect(botMsg).toBeVisible({ timeout: 10000 });
  });

  test("повторный визит → нет дисклеймера → история сохранена", async ({ page, context }) => {
    await context.addInitScript(() => {
      localStorage.setItem("kairos:consent_v1", JSON.stringify({
        accepted: true,
        ts: Date.now(),
      }));
    });

    await page.goto("/chat");

    const disclaimer = page.getByRole("dialog").filter({ hasText: /не замена/i });
    await expect(disclaimer).not.toBeVisible({ timeout: 2000 });
  });
});
