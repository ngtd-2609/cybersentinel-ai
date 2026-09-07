import { expect, test } from "@playwright/test";

import {
  analystUser,
  authenticate,
  dashboardSummary,
  fulfillJson,
} from "./fixtures";

const incident = {
  id: 7,
  workspace: "SANDBOX",
  owner_user_id: 2,
  sandbox_expires_at: "2026-09-07T10:00:00Z",
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
  display_id: "CS-2026-0007",
  correlation_key: "asset:prod-web-01:ssh",
  event_count: 2,
  priority: "P1",
  assignee_user_id: null,
  tags: ["credential-access"],
  resolution_reason: null,
  first_seen_at: "2026-09-03T09:58:00Z",
  last_event_at: "2026-09-03T10:00:00Z",
  resolved_at: null,
  affected_assets: [{
    id: "asset-prod-web-01",
    hostname: "prod-web-01",
    primary_ip: "203.0.113.20",
    operating_system: "Ubuntu 24.04",
    environment: "PROD",
    criticality: "CRITICAL",
    owner_team: "Platform Team",
    internet_facing: true,
    status: "ONLINE",
    last_seen_at: "2026-09-03T10:00:00Z",
  }],
  related_detections: [],
  created_at: "2026-09-03T10:00:00Z",
};

test.beforeEach(async ({ page }) => {
  await authenticate(page, analystUser);
});

test("analyst promotes a detection, investigates it, and resolves the incident", async ({
  page,
}) => {
  let timelineAdded = false;
  let responseAdded = false;
  let copilotContext = "";
  let currentIncident = incident;
  await page.route("**/api/backend/**", async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();

    if (url.pathname === "/api/backend/events/page" && method === "GET") {
      return fulfillJson(route, {
        items: [
          {
            ...incident.detection_event,
            workspace: "SANDBOX",
            owner_user_id: 2,
            sandbox_expires_at: "2026-09-07T10:00:00Z",
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
      expect(route.request().postDataJSON()).toEqual({
        status: "RESOLVED",
        resolution_reason: "Validated evidence and completed simulated containment.",
      });
      currentIncident = {
        ...currentIncident,
        status: "RESOLVED",
        resolution_reason: "Validated evidence and completed simulated containment.",
      };
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
    if (url.pathname === "/api/backend/incidents/7/responses" && method === "GET") {
      return fulfillJson(route, responseAdded ? [{
        id: 1,
        action: "BLOCK_SOURCE_IP",
        target: "198.51.100.42",
        status: "SIMULATED_SUCCESS",
        result: "Simulation completed; no external system was modified.",
        simulation: true,
        created_at: "2026-09-03T10:06:00Z",
        completed_at: "2026-09-03T10:06:00Z",
      }] : []);
    }
    if (url.pathname === "/api/backend/incidents/7/responses/simulate" && method === "POST") {
      expect(route.request().postDataJSON()).toEqual({
        action: "BLOCK_SOURCE_IP",
        target: "198.51.100.42",
      });
      responseAdded = true;
      return fulfillJson(route, {
        id: 1,
        action: "BLOCK_SOURCE_IP",
        target: "198.51.100.42",
        status: "SIMULATED_SUCCESS",
        result: "Simulation completed; no external system was modified.",
        simulation: true,
        created_at: "2026-09-03T10:06:00Z",
        completed_at: "2026-09-03T10:06:00Z",
      }, 201);
    }
    if (url.pathname === "/api/backend/threat-intel/ip/198.51.100.42") {
      return fulfillJson(route, {
        provider: "abuseipdb",
        indicator: "198.51.100.42",
        reputation: "MALICIOUS",
        abuse_confidence: 92,
        country: "US",
        reports: 47,
        cached: false,
        available: true,
        error: null,
      });
    }
    if (url.pathname === "/api/backend/copilot/ask" && method === "POST") {
      const payload = route.request().postDataJSON();
      copilotContext = payload.alert_context;
      return fulfillJson(route, {
        answer: "AbuseIPDB reports a malicious source. Validate credentials and contain the source.",
        model: "grounded-test",
        sources: [],
      });
    }
    return fulfillJson(route, { detail: "Unexpected E2E request" }, 500);
  });

  await page.goto("/events");
  await page.getByRole("button", { name: "Create" }).click();
  await expect(page).toHaveURL(/\/incidents\/7$/);
  await expect(page.getByText("198.51.100.42", { exact: true })).toBeVisible();
  await expect(page.getByText("96/100")).toBeVisible();
  await expect(page.getByText("prod-web-01")).toBeVisible();
  await expect(page.getByText("92%")).toBeVisible();

  await page.getByRole("button", { name: "Analyze incident" }).click();
  await expect(page.getByText(/AbuseIPDB reports a malicious source/)).toBeVisible();
  expect(JSON.parse(copilotContext)).toMatchObject({
    threat_intelligence: {
      provider: "abuseipdb",
      indicator: "198.51.100.42",
      abuse_confidence: 92,
    },
  });

  await page.getByPlaceholder("Describe the analyst action...").fill(
    "Validated source IP against authentication logs.",
  );
  await page.getByRole("button", { name: "Add entry" }).click();
  await expect(page.getByText("Validated source IP against authentication logs.")).toBeVisible();

  await page.getByPlaceholder("198.51.100.42").fill("198.51.100.42");
  await page.getByRole("button", { name: "Simulate" }).click();
  await expect(page.getByText(/no external system was modified/i)).toBeVisible();

  await page.getByPlaceholder("Describe what was verified, contained or remediated...").fill(
    "Validated evidence and completed simulated containment.",
  );
  await page.getByRole("button", { name: "Confirm resolution" }).click();
  await expect(page.getByText("RESOLVED").first()).toBeVisible();
});

test("event detail shows live AbuseIPDB enrichment", async ({ page }) => {
  await page.route("**/api/backend/events/19", (route) => fulfillJson(route, {
    ...incident.detection_event,
    destination_ip: "203.0.113.20",
    destination_port: 22,
    classifier_confidence: 0.98,
    anomaly_score: 0.91,
    rule_score: 0.85,
    requires_review: true,
    asset: null,
    created_at: incident.created_at,
  }));
  await page.route("**/api/backend/threat-intel/ip/198.51.100.42", (route) => fulfillJson(route, {
    provider: "AbuseIPDB",
    indicator: "198.51.100.42",
    reputation: "MALICIOUS",
    abuse_confidence: 92,
    country: "US",
    reports: 47,
    cached: false,
    available: true,
    error: null,
  }));

  await page.goto("/events/19");
  await expect(page.getByText("AbuseIPDB intelligence · 198.51.100.42")).toBeVisible();
  await expect(page.getByText("92%")).toBeVisible();
  await expect(page.getByText("US · AbuseIPDB (live)")).toBeVisible();
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
