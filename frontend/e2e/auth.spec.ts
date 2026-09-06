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

test("a visitor can register a safe viewer account and enter the dashboard", async ({ page }) => {
  let signedIn = false;
  await page.route("**/api/auth/me", (route) =>
    signedIn ? fulfillJson(route, viewerUser) : fulfillJson(route, { detail: "Not authenticated" }, 401),
  );
  await page.route("**/api/auth/register", async (route) => {
    signedIn = true;
    await page.context().addCookies([{
      name: "cybersentinel_access_token",
      value: "registered-viewer-token",
      url: "http://127.0.0.1:3100",
      httpOnly: true,
      sameSite: "Lax",
    }]);
    await fulfillJson(route, viewerUser, 201);
  });
  await mockDashboard(page);

  await page.goto("/login");
  await page.getByRole("button", { name: "Create account" }).click();
  await page.getByLabel("Full name").fill("Portfolio Viewer");
  await page.getByLabel("Username").fill("portfolio-viewer");
  await page.getByLabel("Email address").fill("viewer@example.test");
  await page.getByLabel("Password", { exact: true }).fill("StrongPassword123!");
  await page.getByLabel("Confirm password").fill("StrongPassword123!");
  await page.getByRole("button", { name: "Create account" }).click();

  await expect(page).toHaveURL("/");
  await expect(page.getByRole("heading", { name: "Security Overview" })).toBeVisible();
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
  await page.context().addCookies([
    {
      name: "cybersentinel_access_token",
      value: "e2e-token",
      url: "http://127.0.0.1:3100",
      httpOnly: true,
      sameSite: "Lax",
    },
  ]);
  await page.getByRole("button", { name: "Sign in securely" }).click();

  await expect(page).toHaveURL("/");
  await expect(page.getByRole("heading", { name: "Security Overview" })).toBeVisible();
});

test("portfolio demo login waits for health and signs in safely", async ({ page }) => {
  let signedIn = false;
  await page.route("**/api/health", (route) =>
    fulfillJson(route, { status: "ready" }),
  );
  await page.route("**/api/auth/me", (route) =>
    signedIn
      ? fulfillJson(route, viewerUser)
      : fulfillJson(route, { detail: "Not authenticated" }, 401),
  );
  await page.route("**/api/auth/demo", async (route) => {
    signedIn = true;
    await page.context().addCookies([
      {
        name: "cybersentinel_access_token",
        value: "portfolio-e2e-token",
        url: "http://127.0.0.1:3100",
        httpOnly: true,
        sameSite: "Lax",
      },
    ]);
    await fulfillJson(route, viewerUser);
  });
  await mockDashboard(page);

  await page.goto("/login");
  const demoButton = page.getByRole("button", {
    name: "Explore with the safe demo account",
  });
  await expect(page.getByText("Portfolio demo services are ready.")).toBeVisible();
  await expect(demoButton).toBeEnabled();
  await demoButton.click();

  await expect(page).toHaveURL("/");
  await expect(page.getByRole("heading", { name: "Security Overview" })).toBeVisible();
});

test("administrator login completes an MFA challenge before navigation", async ({ page }) => {
  await page.route("**/api/auth/me", (route) =>
    fulfillJson(route, { detail: "Not authenticated" }, 401),
  );
  await page.route("**/api/auth/login", (route) =>
    fulfillJson(
      route,
      { mfa_required: true, mfa_token: "test-mfa-token", expires_in: 300 },
      202,
    ),
  );
  await page.route("**/api/auth/mfa/verify", (route) => fulfillJson(route, adminUser));
  await page.route("**/api/backend/dashboard/summary", (route) =>
    fulfillJson(route, dashboardSummary),
  );

  await page.goto("/login");
  await page.getByLabel("Email address").fill(adminUser.email);
  await page.getByLabel("Password").fill("valid-test-password");
  await page.getByRole("button", { name: "Sign in securely" }).click();

  await expect(page.getByLabel("Authenticator or recovery code")).toBeVisible();
  await page.getByLabel("Authenticator or recovery code").fill("123456");
  await page.context().addCookies([
    {
      name: "cybersentinel_access_token",
      value: "e2e-token",
      url: "http://127.0.0.1:3100",
      httpOnly: true,
      sameSite: "Lax",
    },
  ]);
  await page.getByRole("button", { name: "Verify MFA" }).click();
  await expect(page).toHaveURL("/");
});

test("signing out clears the active session", async ({ page }) => {
  let signedOut = false;
  await page.context().addCookies([
    {
      name: "cybersentinel_access_token",
      value: "e2e-token",
      url: "http://127.0.0.1:3100",
      httpOnly: true,
      sameSite: "Lax",
    },
  ]);
  await page.route("**/api/auth/me", (route) =>
    signedOut
      ? fulfillJson(route, { detail: "Not authenticated" }, 401)
      : fulfillJson(route, adminUser),
  );
  await page.route("**/api/auth/logout", async (route) => {
    signedOut = true;
    await page.context().clearCookies();
    await route.fulfill({ status: 204 });
  });
  await mockDashboard(page);

  await page.goto("/");
  await page.getByRole("button", { name: "Sign out" }).click();

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByLabel("Email address")).toBeVisible();
});

test("an expired API session returns the user to login", async ({ page }) => {
  let expired = false;
  let eventRequests = 0;
  await page.context().addCookies([
    {
      name: "cybersentinel_access_token",
      value: "expired-e2e-token",
      url: "http://127.0.0.1:3100",
      httpOnly: true,
      sameSite: "Lax",
    },
  ]);
  await page.route("**/api/auth/me", (route) =>
    expired
      ? fulfillJson(route, { detail: "Not authenticated" }, 401)
      : fulfillJson(route, adminUser),
  );
  await page.route("**/api/backend/events/page?*", async (route) => {
    eventRequests += 1;
    if (eventRequests === 1) {
      return fulfillJson(route, { items: [], total: 0, limit: 25, offset: 0 });
    }
    expired = true;
    await page.context().clearCookies();
    return fulfillJson(route, { detail: "Session expired" }, 401);
  });

  await page.goto("/events");
  await expect(page.getByRole("heading", { name: "Detection Events" })).toBeVisible();
  await page.getByRole("button", { name: "Refresh" }).click();

  await expect(page).toHaveURL(/\/login\?returnTo=%2Fevents$/);
  await expect(page.getByLabel("Email address")).toBeVisible();
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

test("dashboard controls work on mobile and expose real destinations", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await authenticate(page, viewerUser);
  await mockDashboard(page);
  await page.route("**/api/backend/incidents?*", (route) => fulfillJson(route, {
    items: [{
      id: 1,
      title: "[DEMO] Ransomware containment",
      severity: "CRITICAL",
      status: "IN_PROGRESS",
      description: "Synthetic incident",
      detection_event_id: 1,
      correlation_key: "demo-ransomware",
      event_count: 1,
      last_event_at: "2026-09-05T18:00:00Z",
      created_at: "2026-09-05T18:00:00Z",
    }],
    total: 1,
    limit: 3,
    offset: 0,
  }));

  await page.goto("/");
  await page.getByRole("button", { name: "Navigation" }).click();
  await expect(page.getByRole("link", { name: "Reports" })).toBeVisible();
  await page.keyboard.press("Escape");
  await page.setViewportSize({ width: 1024, height: 900 });
  await page.getByRole("button", { name: "Switch to Vietnamese" }).click();
  await expect(page.getByRole("heading", { name: "Tổng quan bảo mật" })).toBeVisible();
  await page.getByRole("button", { name: "Chuyển sang tiếng Anh" }).click();
  await page.getByRole("button", { name: "Notifications" }).click();
  await expect(page.getByText("No new notifications")).toBeVisible();
  await expect(page.getByRole("link", { name: /Ransomware containment/ })).toHaveAttribute("href", "/incidents/1");
  await expect(page.getByRole("link", { name: /Open SOC Copilot|Mở Trợ lý SOC/ })).toHaveAttribute(
    "href",
    "/copilot",
  );
});
