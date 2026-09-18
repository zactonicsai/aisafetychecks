import { test, expect } from "@playwright/test";

test("factory dashboard loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "AI Software Factory", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Pipeline lab" })).toBeVisible();
});

