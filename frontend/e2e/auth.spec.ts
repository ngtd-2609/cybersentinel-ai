import { expect, test } from "@playwright/test";

import {
  adminUser,
  authenticate,
  dashboardSummary,
  fulfillJson,
  mockDashboard,
  viewerUser,
} from "./fixtures";

test("protected routes redirect anonymous users to login", async ({ page }) => {
  await page.route("**/api/auth/me", (route) =>
    fulfillJson(route, { detail: "Not authenticated" }, 401),
  );
  await page.goto("/incidents");

  await expect(page).toHaveURL(/\/login\?returnTo=%2Fincidents/);
});

test("login reports invalid credentials", async ({ page }) => {
  await page.route("**/api/auth/me", (route) =>
    fulfillJson(route, { detail: "Not authenticated" }, 401),
  );
  await page.route("**/api/auth/login", (route) =>
    fulfillJson(route, { detail: "Invalid credentials" }, 401),
  );

  await page.goto("/login");
  await page.getByLabel("Email address").fill("invalid@example.test");
  await page.getByLabel("Password").fill("wrong-password");
  await page.getByRole("button", { name: "Sign in securely" }).click();

  await expect(page.getByRole("alert").filter({ hasText: "Invalid credentials" })).toHaveText(
    "Invalid credentials",
  );
});

test("successful login returns to the requested page", async ({ page }) => {
  let signedIn = false;
  await page.route("**/api/auth/me", (route) =>
    signedIn
      ? fulfillJson(route, adminUser)
      : fulfillJson(route, { detail: "Not authenticated" }, 401),
  );
  await page.route("**/api/auth/login", async (route) => {
    signedIn = true;
    await page.context().addCookies([
      {
        name: "cybersentinel_access_token",
        value: "e2e-token",
        url: "http://127.0.0.1:3100",
        httpOnly: true,
        sameSite: "Lax",
      },
    ]);
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(adminUser),
    });
  });
  await page.route("**/api/backend/dashboard/summary", (route) =>
    fulfillJson(route, dashboardSummary),
  );

  await page.goto("/login?returnTo=%2F");
  await page.getByLabel("Email address").fill(adminUser.email);
  await page.getByLabel("Password").fill("valid-test-password");
  await page.getByRole("button", { name: "Sign in securely" }).click();

  await expect(page).toHaveURL("/");
  await expect(page.getByRole("heading", { name: "Security Overview" })).toBeVisible();
});

test("administration navigation is role-aware", async ({ page }) => {
  await authenticate(page, viewerUser);
  await mockDashboard(page);
  await page.goto("/");
  await expect(page.getByRole("link", { name: "Users & Roles" })).toHaveCount(0);

  await page.unroute("**/api/auth/me");
  await page.route("**/api/auth/me", (route) => fulfillJson(route, adminUser));
  await page.reload();
  await expect(page.getByRole("link", { name: "Users & Roles" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Audit Logs" })).toBeVisible();
});

test("login remains usable at a mobile viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/api/auth/me", (route) =>
    fulfillJson(route, { detail: "Not authenticated" }, 401),
  );
  await page.goto("/login");

  await expect(page.getByLabel("Email address")).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign in securely" })).toBeVisible();
});
