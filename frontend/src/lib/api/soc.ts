import { apiFetch } from "@/lib/api/client";
import type { DetectionEvent, DashboardSummary } from "@/lib/api/dashboard";

export interface DetectionEventPage {
  items: DetectionEvent[];
  total: number;
  limit: number;
  offset: number;
}

export type SimulationScenario =
  | "RANSOMWARE"
  | "SSH-BRUTE-FORCE"
  | "PORT-SCAN"
  | "PHISHING"
  | "DATA-EXFILTRATION";

export interface SandboxSimulation {
  event: DetectionEvent;
  incident_id: number | null;
  expires_at: string;
}

export async function simulateEvent(payload: {
  scenario: SimulationScenario;
  source_ip?: string;
  destination_ip?: string;
  hostname?: string;
}): Promise<SandboxSimulation> {
  const response = await apiFetch("/events/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return jsonResponse<SandboxSimulation>(response, "Unable to simulate event");
}

export async function resetSandbox(): Promise<{
  events_deleted: number;
  incidents_deleted: number;
}> {
  const response = await apiFetch("/events/sandbox/reset", { method: "POST" });
  return jsonResponse(response, "Unable to reset sandbox");
}

export interface HealthStatus {
  status: string;
  service?: string;
}

export interface ComponentStatus {
  components: { name: string; state: string; basis: string }[];
  queues: Record<string, number>;
}

export async function getComponentStatus(): Promise<ComponentStatus> {
  const response = await apiFetch("/status/components");
  return jsonResponse<ComponentStatus>(response, "Unable to load component status");
}

export interface AssetOverview {
  id: string;
  hostname: string;
  primary_ip: string | null;
  operating_system: string | null;
  environment: string;
  criticality: string;
  owner_team: string | null;
  internet_facing: boolean;
  status: string;
  last_seen_at: string | null;
  detections_count: number;
  active_incidents_count: number;
}

export async function getAssetOverview(query = ""): Promise<AssetOverview[]> {
  const params = query.trim() ? `?query=${encodeURIComponent(query.trim())}` : "";
  const response = await apiFetch(`/assets/overview${params}`);
  return jsonResponse<AssetOverview[]>(response, "Unable to load assets");
}

async function jsonResponse<T>(response: Response, message: string): Promise<T> {
  if (!response.ok) {
    throw new Error(`${message} (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function getDetectionEvents(limit = 100): Promise<DetectionEventPage> {
  const response = await apiFetch(`/events/page?limit=${limit}&offset=0`);
  return jsonResponse<DetectionEventPage>(response, "Unable to load detections");
}

export async function getHealth(): Promise<HealthStatus> {
  const response = await apiFetch("/health");
  return jsonResponse<HealthStatus>(response, "API health check failed");
}

export async function getPrometheusMetrics(): Promise<string> {
  const response = await apiFetch("/metrics", {
    headers: { Accept: "text/plain" },
  });
  if (!response.ok) {
    throw new Error(`Metrics request failed (${response.status})`);
  }
  return response.text();
}

export function metricValue(metrics: string, name: string): number | null {
  const line = metrics
    .split("\n")
    .find((item) => item.startsWith(`${name} `));
  if (!line) return null;
  const value = Number(line.slice(name.length + 1));
  return Number.isFinite(value) ? value : null;
}

export function metricSum(metrics: string, name: string): number {
  return metrics
    .split("\n")
    .filter((line) => line.startsWith(`${name}{`) || line.startsWith(`${name} `))
    .reduce((total, line) => total + (Number(line.split(" ").at(-1)) || 0), 0);
}

export function summaryToRows(summary: DashboardSummary): string[][] {
  return [
    ["Metric", "Value"],
    ["Total events", String(summary.total_events)],
    ["Critical alerts", String(summary.critical_alerts)],
    ["High alerts", String(summary.high_alerts)],
    ["Requires review", String(summary.requires_review)],
    ["Average risk score", summary.average_risk_score.toFixed(2)],
  ];
}

export function downloadCsv(filename: string, rows: string[][]): void {
  const csv = rows
    .map((row) =>
      row.map((cell) => `"${cell.replaceAll('"', '""')}"`).join(","),
    )
    .join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
