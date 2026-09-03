import type { Page, Route } from "@playwright/test";

export interface TestUser {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role: string;
}

export const adminUser: TestUser = {
  id: 1,
  email: "admin@example.test",
  username: "admin",
  full_name: "E2E Administrator",
  role: "ADMIN",
};

export const analystUser: TestUser = {
  id: 2,
  email: "analyst@example.test",
  username: "analyst",
  full_name: "E2E Analyst",
  role: "ANALYST",
};

export const viewerUser: TestUser = {
  id: 3,
  email: "viewer@example.test",
  username: "viewer",
  full_name: "E2E Viewer",
  role: "VIEWER",
};

export const dashboardSummary = {
  total_events: 3,
  critical_alerts: 1,
  high_alerts: 1,
  medium_alerts: 1,
  low_alerts: 0,
  requires_review: 2,
  average_risk_score: 83.4,
  top_attack_types: [{ name: "SSH-BRUTE-FORCE", count: 2 }],
  top_threat_sources: [
    { source_ip: "198.51.100.42", count: 2, max_risk_score: 96 },
  ],
  timeline: [
    { time: "2026-09-03T10:00:00Z", total: 3, critical: 1, high: 1, medium: 1, low: 0 },
  ],
  recent_events: [],
};

export async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

export async function authenticate(page: Page, user: TestUser) {
  await page.context().addCookies([
    {
      name: "cybersentinel_access_token",
      value: "e2e-token",
      url: "http://127.0.0.1:3100",
      httpOnly: true,
      sameSite: "Lax",
    },
  ]);
  await page.route("**/api/auth/me", (route) => fulfillJson(route, user));
}

export async function mockDashboard(page: Page) {
  await page.route("**/api/backend/dashboard/summary", (route) =>
    fulfillJson(route, dashboardSummary),
  );
}
