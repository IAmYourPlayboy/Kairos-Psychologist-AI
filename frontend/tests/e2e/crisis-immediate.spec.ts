import { test, expect } from "@playwright/test";

/**
 * Кризисный поток (immediate): отправка триггерного текста → автооткрытие
 * CrisisPanel → видны контакты → Esc закрывает.
 */
test.describe("Crisis immediate flow", () => {
  test.beforeEach(async ({ context }) => {
    await context.addInitScript(() => {
      localStorage.setItem("kairos:consent_v1", JSON.stringify({
        accepted: true,
        ts: Date.now(),
      }));
    });
  });

  test("отправка 'хочу умереть' → CrisisPanel автоматически открыт + 112 виден + Esc закрывает", async ({ page }) => {
    await page.goto("/chat");

    const input = page.getByLabel("Сообщение");
    await input.fill("хочу умереть");
    // Клик по кнопке «Отправить» надёжнее Enter (нет race с autofocus)
    await page.getByRole("button", { name: "Отправить" }).click();

    // CrisisPanel должен открыться автоматически (по immediate в response)
    const crisisDialog = page.getByRole("dialog").filter({ hasText: /кому позвонить/i });
    await expect(crisisDialog).toBeVisible({ timeout: 10000 });

    // Номер 112 должен быть виден
    await expect(page.getByText("112").first()).toBeVisible();

    // Esc закрывает
    await page.keyboard.press("Escape");
    await expect(crisisDialog).not.toBeVisible({ timeout: 2000 });
  });

  test("SOS-кнопка открывает CrisisPanel при normal сообщении", async ({ page }) => {
    await page.goto("/chat");

    const input = page.getByLabel("Сообщение");
    await input.fill("привет");
    await page.getByRole("button", { name: "Отправить" }).click();

    // Ждём ответа
    await page.waitForTimeout(2000);

    // Кликаем SOS (aria-label: «Открыть кризисные контакты»)
    await page.getByRole("button", { name: /кризисные контакты/i }).click();

    // CrisisPanel открыт даже при normal
    const crisisDialog = page.getByRole("dialog").filter({ hasText: /кому позвонить/i });
    await expect(crisisDialog).toBeVisible();
    await expect(page.getByText("112").first()).toBeVisible();
  });
});
