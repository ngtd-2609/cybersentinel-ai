export interface Incident {
  id: number;
  title: string;
  severity: string;
  status: string;
  description: string | null;
  detection_event_id: number | null;
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

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export async function getIncidents(
  limit: number = 25,
  offset: number = 0,
): Promise<IncidentPage> {
  const response = await fetch(`${API_URL}/incidents?limit=${limit}&offset=${offset}`, {
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


export async function getIncidentById(
  id: number,
): Promise<Incident> {
  const response = await fetch(`${API_URL}/incidents/${id}`, {
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
  const response = await fetch(`${API_URL}/incidents/${id}`, {
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
