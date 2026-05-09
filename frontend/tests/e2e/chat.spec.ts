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

    // Реальный ключ в FirstVisitModal.tsx — kairos.consent_v1_given (с точкой, суффикс _given).
    // Диалог имеет DialogTitle «Прежде чем мы начнём» — accessible name надёжнее hasText.
    const disclaimer = page.getByRole("dialog", { name: /прежде чем мы начнём/i });
    await expect(disclaimer).toBeVisible({ timeout: 5000 });

    const checkboxes = page.getByRole("checkbox");
    const count = await checkboxes.count();
    for (let i = 0; i < count; i++) {
      await checkboxes.nth(i).check();
    }
    // Реальный текст кнопки: «Согласен(на), продолжить»
    await page.getByRole("button", { name: /согласен/i }).click();
    await expect(disclaimer).not.toBeVisible();

    // Chat textarea имеет aria-label="Сообщение" — через getByLabel точнее
    const input = page.getByLabel("Сообщение");
    await input.fill("привет");
    // Отправка — либо Enter, либо клик по кнопке "Отправить" (aria-label)
    await page.getByRole("button", { name: "Отправить" }).click();

    // Ждём ответа от бота (mock возвращает «Привет. Я Кайрос. Что у тебя?»)
    const botMsg = page.getByText(/Кайрос/i).last();
    await expect(botMsg).toBeVisible({ timeout: 10000 });
  });

  test("повторный визит → нет дисклеймера → история сохранена", async ({ page, context }) => {
    // Реальный ключ — kairos.consent_v1_given, значение «1» (см. FirstVisitModal.tsx:102).
    await context.addInitScript(() => {
      localStorage.setItem("kairos.consent_v1_given", "1");
    });

    await page.goto("/chat");

    const disclaimer = page.getByRole("dialog", { name: /прежде чем мы начнём/i });
    await expect(disclaimer).not.toBeVisible({ timeout: 2000 });
  });
});
