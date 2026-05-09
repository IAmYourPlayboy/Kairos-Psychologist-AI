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

    const input = page.getByRole("textbox");
    await input.fill("хочу умереть");
    await input.press("Enter");

    const crisisDialog = page.getByRole("dialog").filter({ hasText: /кому позвонить/i });
    await expect(crisisDialog).toBeVisible({ timeout: 10000 });

    await expect(page.getByText("112").first()).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(crisisDialog).not.toBeVisible({ timeout: 2000 });
  });

  test("SOS-кнопка открывает CrisisPanel при normal сообщении", async ({ page }) => {
    await page.goto("/chat");

    const input = page.getByRole("textbox");
    await input.fill("привет");
    await input.press("Enter");

    await page.waitForTimeout(2000);

    await page.getByRole("button", { name: /кризисные контакты|sos/i }).click();

    const crisisDialog = page.getByRole("dialog").filter({ hasText: /кому позвонить/i });
    await expect(crisisDialog).toBeVisible();
    await expect(page.getByText("112").first()).toBeVisible();
  });
});
