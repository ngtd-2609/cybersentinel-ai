import { apiFetch } from "@/lib/api/client";
import type { DetectionEvent, DashboardSummary } from "@/lib/api/dashboard";

export interface DetectionEventPage {
  items: DetectionEvent[];
  total: number;
  limit: number;
  offset: number;
}

export interface HealthStatus {
  status: string;
  service?: string;
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
