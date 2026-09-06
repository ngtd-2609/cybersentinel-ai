import { apiFetch } from "@/lib/api/client";

export interface DetectionBrief {
  id: number;
  source_ip: string | null;
  predicted_label: string;
  risk_score: number;
  severity: string;
}

export interface Incident {
  id: number;
  display_id: string | null;
  workspace: string;
  owner_user_id: number | null;
  title: string;
  severity: string;
  status: string;
  description: string | null;
  detection_event_id: number | null;
  detection_event?: DetectionBrief | null;
  correlation_key: string | null;
  event_count: number;
  priority: string;
  assignee_user_id: number | null;
  tags: string[];
  resolution_reason: string | null;
  first_seen_at: string | null;
  last_event_at: string | null;
  resolved_at: string | null;
  affected_assets: Asset[];
  related_detections: DetectionBrief[];
  created_at: string;
}

export interface Asset {
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
}


export interface IncidentPage {
  items: Incident[];
  total: number;
  limit: number;
  offset: number;
}

export interface IncidentCreate {
  title: string;
  severity: string;
  status?: string;
  description?: string | null;
  detection_event_id?: number | null;
}

export async function getIncidents(
  limit: number = 25,
  offset: number = 0,
  filters: Record<string, string> = {},
): Promise<IncidentPage> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  Object.entries(filters).forEach(([key, value]) => {
    if (value && value !== "ALL") params.set(key, value);
  });
  const response = await apiFetch(`/incidents?${params.toString()}`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(
      `Incident API request failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<IncidentPage>;
}

export async function createIncident(
  payload: IncidentCreate,
): Promise<Incident> {
  const response = await apiFetch("/incidents", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(
      `Create incident failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<Incident>;
}


export async function getIncidentById(
  id: number,
): Promise<Incident> {
  const response = await apiFetch(`/incidents/${id}`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(
      `Incident detail request failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<Incident>;
}


export async function updateIncidentStatus(
  id: number,
  status: string,
): Promise<Incident> {
  return updateIncident(id, { status });
}

export async function updateIncident(
  id: number,
  payload: Record<string, unknown>,
): Promise<Incident> {
  const response = await apiFetch(`/incidents/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(
      `Update incident failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<Incident>;
}

export interface ResponseAction {
  id: number;
  action: string;
  target: string;
  status: string;
  result: string;
  simulation: boolean;
  created_at: string;
  completed_at: string | null;
}

export async function getResponseActions(id: number): Promise<ResponseAction[]> {
  const response = await apiFetch(`/incidents/${id}/responses`);
  if (!response.ok) throw new Error("Unable to load response actions");
  return response.json() as Promise<ResponseAction[]>;
}

export async function simulateResponse(
  id: number,
  action: string,
  target: string,
): Promise<ResponseAction> {
  const response = await apiFetch(`/incidents/${id}/responses/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ action, target }),
  });
  if (!response.ok) throw new Error(`Response simulation failed with status ${response.status}`);
  return response.json() as Promise<ResponseAction>;
}

export interface ThreatIntel {
  provider: string;
  indicator: string;
  reputation: string;
  abuse_confidence: number | null;
  country: string | null;
  reports: number | null;
  cached: boolean;
  available: boolean;
  error: string | null;
}

export async function getIpThreatIntel(ip: string): Promise<ThreatIntel> {
  const response = await apiFetch(`/threat-intel/ip/${encodeURIComponent(ip)}`);
  if (!response.ok) throw new Error("Unable to enrich source IP");
  return response.json() as Promise<ThreatIntel>;
}


export interface IncidentTimeline {
  id: number;
  incident_id: number;
  action: string;
  description: string;
  created_at: string;
}

export async function getIncidentTimeline(
  id: number,
): Promise<IncidentTimeline[]> {
  const response = await apiFetch(
    `/incidents/${id}/timeline`,
    {
      headers: {
        Accept: "application/json",
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Timeline request failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<IncidentTimeline[]>;
}

export async function createIncidentTimeline(
  id: number,
  action: string,
  description: string,
): Promise<IncidentTimeline> {
  const response = await apiFetch(`/incidents/${id}/timeline`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ action, description }),
  });

  if (!response.ok) {
    throw new Error(`Timeline update failed with status ${response.status}`);
  }

  return response.json() as Promise<IncidentTimeline>;
}


export interface CopilotResponse {
  answer: string;
  model: string;
  sources: {
    document_id: string;
    title: string;
    source: string;
    score: number;
  }[];
}

export async function askCopilot(
  question: string,
  alertContext: string,
): Promise<CopilotResponse> {
  const response = await apiFetch(
    "/copilot/ask",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        question,
        alert_context: alertContext,
        top_k: 4,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(
      `Copilot request failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<CopilotResponse>;
}
