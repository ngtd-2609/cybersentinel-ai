import { apiFetch } from "@/lib/api/client";

export interface AlertRule {
  id: number;
  name: string;
  enabled: boolean;
  priority: number;
  min_risk_score: number;
  severities: string[];
  label_pattern: string | null;
  require_review: boolean;
  auto_create_incident: boolean;
  notification_channels: string[];
  created_at: string;
  updated_at: string;
}

export async function getAlertRules(): Promise<AlertRule[]> {
  const response = await apiFetch("/alert-rules");
  if (!response.ok) throw new Error("Unable to load detection rules");
  return response.json() as Promise<AlertRule[]>;
}

export async function updateAlertRule(id: number, payload: Partial<AlertRule>): Promise<AlertRule> {
  const response = await apiFetch(`/alert-rules/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`Rule update failed with status ${response.status}`);
  return response.json() as Promise<AlertRule>;
}
