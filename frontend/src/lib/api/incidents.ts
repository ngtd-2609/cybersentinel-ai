import { apiFetch } from "@/lib/api/client";

export interface Incident {
  id: number;
  title: string;
  severity: string;
  status: string;
  description: string | null;
  detection_event_id: number | null;
  detection_event?: {
    id: number;
    source_ip: string | null;
    predicted_label: string;
    risk_score: number;
    severity: string;
  } | null;
  correlation_key: string | null;
  event_count: number;
  last_event_at: string | null;
  created_at: string;
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
): Promise<IncidentPage> {
  const response = await apiFetch(`/incidents?limit=${limit}&offset=${offset}`, {
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
  const response = await apiFetch(`/incidents/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ status }),
  });

  if (!response.ok) {
    throw new Error(
      `Update incident failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<Incident>;
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
