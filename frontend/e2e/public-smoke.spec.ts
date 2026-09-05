import { expect, test } from "@playwright/test";

test.describe("public portfolio smoke", () => {
  test.skip(
    process.env.PUBLIC_SMOKE !== "true",
    "Set PUBLIC_SMOKE=true and PLAYWRIGHT_BASE_URL to the deployed frontend URL.",
  );

  test("reviewer can traverse the live SOC demo", async ({ page }) => {
    test.setTimeout(180_000);
    const captureReadme = process.env.CAPTURE_README === "true";
    if (captureReadme) {
      await page.setViewportSize({ width: 1440, height: 900 });
    }

    await page.goto("/login");
    const demoButton = page.getByRole("button", {
      name: "Explore with the safe demo account",
    });
    await expect(demoButton).toBeEnabled({ timeout: 120_000 });
    await demoButton.click();
    await expect(
      page.getByRole("heading", { name: "Security Overview" }),
    ).toBeVisible();
    if (captureReadme) {
      await page.screenshot({ path: "../docs/assets/dashboard.png" });
    }

    await page.goto("/events");
    await expect(
      page.getByRole("heading", { name: "Detection Events" }),
    ).toBeVisible();
    await expect(page.getByRole("link", { name: "EVT-00001" })).toBeVisible();

    await page.goto("/incidents");
    await expect(
      page.getByRole("heading", { name: "Incident Management" }),
    ).toBeVisible();
    await expect(page.getByText("[DEMO] Ransomware containment")).toBeVisible();
    if (captureReadme) {
      await page.screenshot({ path: "../docs/assets/incidents.png" });
    }

    await page.goto("/threat-intel");
    await expect(
      page.getByRole("heading", { name: "Threat Intelligence" }),
    ).toBeVisible();
    await expect(page.getByText("Observed source indicators")).toBeVisible();

    await page.goto("/copilot");
    await expect(page.getByRole("heading", { name: "SOC Copilot" })).toBeVisible();
    await page.getByRole("button", { name: "Ask Copilot" }).click();
    await expect(page.getByRole("heading", { name: "Analysis" })).toBeVisible();
    await expect(page.getByText("deterministic-fallback")).toBeVisible();
    if (captureReadme) {
      await page.screenshot({ path: "../docs/assets/copilot.png" });
    }

    await page.goto("/reports");
    await expect(page.getByRole("heading", { name: "Reports" })).toBeVisible();
    await expect(page.getByText("8 RECORDS")).toBeVisible();
    await expect(page.getByText("3 RECORDS")).toBeVisible();
  });
});
