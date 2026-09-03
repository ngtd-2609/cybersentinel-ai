export const AUTH_COOKIE_NAME = "cybersentinel_access_token";

export const WRITE_ROLES = [
  "ADMIN",
  "SENIOR_ANALYST",
  "ANALYST",
] as const;

export interface AuthUser {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: string;
}

export function canWrite(role: string): boolean {
  return WRITE_ROLES.some((allowedRole) => allowedRole === role);
}

export function formatRole(role: string): string {
  return role
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
