export const BACKEND_API_URL = (
  process.env.CYBERSENTINEL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8001"
).replace(/\/$/, "");

export const AUTH_COOKIE_OPTIONS = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
  maxAge: 60 * 60,
};
