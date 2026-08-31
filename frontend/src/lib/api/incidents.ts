export interface Incident {
  id: number;
  title: string;
  severity: string;
  status: string;
  description: string | null;
  detection_event_id: number | null;
  created_at: string;
}

export interface IncidentCreate {
  title: string;
  severity: string;
  status?: string;
  description?: string | null;
  detection_event_id?: number | null;
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export async function getIncidents(): Promise<Incident[]> {
  const response = await fetch(`${API_URL}/incidents`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(
      `Incident API request failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<Incident[]>;
}

export async function createIncident(
  payload: IncidentCreate,
): Promise<Incident> {
  const response = await fetch(`${API_URL}/incidents`, {
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
