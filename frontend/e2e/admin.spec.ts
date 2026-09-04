import { expect, test } from "@playwright/test";

import { adminUser, authenticate, fulfillJson } from "./fixtures";

const analyst = {
  id: 2,
  email: "analyst@example.test",
  username: "analyst",
  full_name: "E2E Analyst",
  role: "ANALYST",
  is_active: true,
};

test.beforeEach(async ({ page }) => {
  await authenticate(page, adminUser);
});

test("administrator disables another user account", async ({ page }) => {
  await page.route("**/api/backend/admin/users", (route) =>
    fulfillJson(route, [{ ...adminUser, is_active: true }, analyst]),
  );
  await page.route("**/api/backend/admin/users/2/status", async (route) => {
    expect(route.request().method()).toBe("PATCH");
    expect(route.request().postDataJSON()).toEqual({ is_active: false });
    await fulfillJson(route, { ...analyst, is_active: false });
  });

  await page.goto("/admin/users");
  const analystRow = page.getByRole("row").filter({ hasText: analyst.email });
  await analystRow.getByRole("button", { name: "Disable" }).click();

  await expect(analystRow.getByText("Disabled")).toBeVisible();
  await expect(analystRow.getByRole("button", { name: "Enable" })).toBeVisible();
});

test("administrator reviews attributable audit records", async ({ page }) => {
  await page.route("**/api/backend/admin/audit-logs?*", (route) =>
    fulfillJson(route, {
      items: [
        {
          id: 11,
          user_id: 1,
          action: "CREATE_INCIDENT",
          target_type: "INCIDENT",
          target_id: 7,
          description: "Created incident from detection event 19.",
          request_id: "request-abc-123",
          ip_address: "203.0.113.9",
          user_agent: "Playwright",
          created_at: "2026-09-03T10:10:00Z",
        },
      ],
      total: 1,
      limit: 25,
      offset: 0,
    }),
  );

  await page.goto("/admin/audit-logs");

  await expect(page.getByText("Create Incident", { exact: true })).toBeVisible();
  await expect(page.getByText("User #1")).toBeVisible();
  await expect(page.getByText("Incident #7")).toBeVisible();
  await expect(page.getByText("Created incident from detection event 19.")).toBeVisible();
  await expect(page.getByText("203.0.113.9 · request-abc-123")).toBeVisible();
});
