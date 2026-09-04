import { apiFetch } from "@/lib/api/client";

export const USER_ROLES = [
  "ADMIN",
  "SENIOR_ANALYST",
  "ANALYST",
  "VIEWER",
] as const;

export interface AdminUser {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
}

export interface AuditLog {
  id: number;
  user_id: number | null;
  action: string;
  target_type: string | null;
  target_id: number | null;
  description: string;
  request_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface AuditLogPage {
  items: AuditLog[];
  total: number;
  limit: number;
  offset: number;
}

async function parseResponse<T>(
  response: Response,
  fallbackMessage: string,
): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? fallbackMessage);
  }

  return response.json() as Promise<T>;
}

export async function getAdminUsers(): Promise<AdminUser[]> {
  const response = await apiFetch("/admin/users");
  return parseResponse<AdminUser[]>(response, "Unable to load users");
}

export async function updateAdminUserRole(
  userId: number,
  role: string,
): Promise<AdminUser> {
  const response = await apiFetch(`/admin/users/${userId}/role`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
  return parseResponse<AdminUser>(response, "Unable to update role");
}

export async function updateAdminUserStatus(
  userId: number,
  isActive: boolean,
): Promise<AdminUser> {
  const response = await apiFetch(`/admin/users/${userId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ is_active: isActive }),
  });
  return parseResponse<AdminUser>(response, "Unable to update account status");
}

export async function getAuditLogs({
  limit = 25,
  offset = 0,
  action,
  targetType,
  userId,
}: {
  limit?: number;
  offset?: number;
  action?: string;
  targetType?: string;
  userId?: number;
} = {}): Promise<AuditLogPage> {
  const parameters = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  if (action) {
    parameters.set("action", action);
  }
  if (targetType) {
    parameters.set("target_type", targetType);
  }
  if (userId) {
    parameters.set("user_id", String(userId));
  }

  const response = await apiFetch(`/admin/audit-logs?${parameters}`);
  return parseResponse<AuditLogPage>(response, "Unable to load audit logs");
}
