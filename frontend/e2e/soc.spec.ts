import { expect, test } from "@playwright/test";

import {
  analystUser,
  authenticate,
  dashboardSummary,
  fulfillJson,
} from "./fixtures";

const incident = {
  id: 7,
  title: "SSH brute-force investigation",
  severity: "CRITICAL",
  status: "OPEN",
  description: "Repeated authentication attempts against the SSH service.",
  detection_event_id: 19,
  detection_event: {
    id: 19,
    source_ip: "198.51.100.42",
    predicted_label: "SSH-BRUTE-FORCE",
    risk_score: 96,
    severity: "CRITICAL",
  },
  created_at: "2026-09-03T10:00:00Z",
};

test.beforeEach(async ({ page }) => {
  await authenticate(page, analystUser);
});

test("analyst promotes a detection, investigates it, and resolves the incident", async ({
  page,
}) => {
  let timelineAdded = false;
  let currentIncident = incident;
  await page.route("**/api/backend/**", async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();

    if (url.pathname === "/api/backend/events/page" && method === "GET") {
      return fulfillJson(route, {
        items: [
          {
            ...incident.detection_event,
            destination_ip: "203.0.113.20",
            destination_port: 22,
            classifier_confidence: 0.98,
            anomaly_score: 0.91,
            rule_score: 0.85,
            requires_review: true,
            created_at: incident.created_at,
          },
        ],
        total: 1,
        limit: 25,
        offset: 0,
      });
    }
    if (url.pathname === "/api/backend/incidents" && method === "POST") {
      expect(route.request().postDataJSON()).toMatchObject({
        detection_event_id: 19,
        severity: "CRITICAL",
        status: "OPEN",
      });
      return fulfillJson(route, currentIncident, 201);
    }
    if (url.pathname === "/api/backend/incidents/7" && method === "GET") {
      return fulfillJson(route, currentIncident);
    }
    if (url.pathname === "/api/backend/incidents/7" && method === "PATCH") {
      expect(route.request().postDataJSON()).toEqual({ status: "RESOLVED" });
      currentIncident = { ...currentIncident, status: "RESOLVED" };
      return fulfillJson(route, currentIncident);
    }
    if (url.pathname === "/api/backend/incidents/7/timeline" && method === "POST") {
      expect(route.request().postDataJSON()).toEqual({
        action: "INVESTIGATION_NOTE",
        description: "Validated source IP against authentication logs.",
      });
      timelineAdded = true;
      return fulfillJson(route, {
        id: 2,
        incident_id: 7,
        action: "INVESTIGATION_NOTE",
        description: "Validated source IP against authentication logs.",
        created_at: "2026-09-03T10:05:00Z",
      });
    }
    if (url.pathname === "/api/backend/incidents/7/timeline" && method === "GET") {
      return fulfillJson(route, timelineAdded ? [{
        id: 2,
        incident_id: 7,
        action: "INVESTIGATION_NOTE",
        description: "Validated source IP against authentication logs.",
        created_at: "2026-09-03T10:05:00Z",
      }] : []);
    }
    return fulfillJson(route, { detail: "Unexpected E2E request" }, 500);
  });

  await page.goto("/events");
  await page.getByRole("button", { name: "Create" }).click();
  await expect(page).toHaveURL(/\/incidents\/7$/);
  await expect(page.getByText("198.51.100.42")).toBeVisible();
  await expect(page.getByText("96/100")).toBeVisible();

  await page.getByPlaceholder("Describe the analyst action...").fill(
    "Validated source IP against authentication logs.",
  );
  await page.getByRole("button", { name: "Add entry" }).click();
  await expect(page.getByText("Validated source IP against authentication logs.")).toBeVisible();

  await page.getByRole("combobox").first().click();
  await page.getByRole("option", { name: "Resolved" }).click();
  await expect(page.getByText("RESOLVED").first()).toBeVisible();
});

test("SOC Copilot renders grounded analysis and sources", async ({ page }) => {
  await page.route("**/api/backend/copilot/ask", async (route) => {
    expect(route.request().postDataJSON()).toMatchObject({ top_k: 4 });
    await fulfillJson(route, {
      answer: "Assessment\nSSH brute-force activity requires credential and source validation.",
      model: "qwen3:4b",
      sources: [{
        document_id: "mitre-t1110",
        title: "T1110 Brute Force",
        source: "MITRE ATT&CK",
        score: 0.91,
      }],
    });
  });

  await page.goto("/copilot");
  await page.getByRole("button", { name: "Ask Copilot" }).click();

  await expect(page.getByText(/SSH brute-force activity/)).toBeVisible();
  await expect(page.getByText("T1110 Brute Force")).toBeVisible();
  await expect(page.getByText("qwen3:4b")).toBeVisible();
});

test("reports export authorized live data as CSV", async ({ page }) => {
  await page.route("**/api/backend/dashboard/summary", (route) =>
    fulfillJson(route, dashboardSummary),
  );
  await page.route("**/api/backend/events/page?*", (route) =>
    fulfillJson(route, { items: [], total: 0, limit: 100, offset: 0 }),
  );
  await page.route("**/api/backend/incidents?*", (route) =>
    fulfillJson(route, { items: [incident], total: 1, limit: 100, offset: 0 }),
  );

  await page.goto("/reports");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download CSV" }).first().click();
  const download = await downloadPromise;

  expect(download.suggestedFilename()).toMatch(/^cybersentinel-summary-\d{4}-\d{2}-\d{2}\.csv$/);
});
