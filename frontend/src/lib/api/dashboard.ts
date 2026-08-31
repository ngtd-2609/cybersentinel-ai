export interface DetectionEvent {
  id: number;
  source_ip: string | null;
  destination_ip: string | null;
  destination_port: number | null;
  predicted_label: string;
  classifier_confidence: number;
  anomaly_score: number;
  rule_score: number;
  risk_score: number;
  severity: string;
  requires_review: boolean;
  created_at: string;
}

export interface DashboardAttackType {
  name: string;
  count: number;
}

export interface DashboardThreatSource {
  source_ip: string;
  count: number;
  max_risk_score: number;
}

export interface DashboardTimelinePoint {
  time: string;
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface DashboardSummary {
  total_events: number;
  critical_alerts: number;
  high_alerts: number;
  medium_alerts: number;
  low_alerts: number;
  requires_review: number;
  average_risk_score: number;
  top_attack_types: DashboardAttackType[];
  top_threat_sources: DashboardThreatSource[];
  timeline: DashboardTimelinePoint[];
  recent_events: DetectionEvent[];
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetch(`${API_URL}/dashboard/summary`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(
      `Dashboard API request failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<DashboardSummary>;
}
