import { NextResponse } from "next/server";

import {
  AUTH_COOKIE_NAME,
  REFRESH_COOKIE_NAME,
} from "@/lib/auth";
import {
  AUTH_COOKIE_OPTIONS,
  BACKEND_API_URL,
} from "@/lib/server/backend";

export interface SessionTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  refresh_expires_in: number;
}

export function setSessionCookies(
  response: NextResponse,
  tokens: SessionTokens,
) {
  response.cookies.set(AUTH_COOKIE_NAME, tokens.access_token, {
    ...AUTH_COOKIE_OPTIONS,
    maxAge: tokens.expires_in,
  });
  response.cookies.set(REFRESH_COOKIE_NAME, tokens.refresh_token, {
    ...AUTH_COOKIE_OPTIONS,
    maxAge: tokens.refresh_expires_in,
  });
}

export function clearSessionCookies(response: NextResponse) {
  response.cookies.delete(AUTH_COOKIE_NAME);
  response.cookies.delete(REFRESH_COOKIE_NAME);
}

export async function refreshSession(
  refreshToken: string,
): Promise<SessionTokens | null> {
  const response = await fetch(`${BACKEND_API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
    cache: "no-store",
  });
  if (!response.ok) {
    return null;
  }
  return (await response.json()) as SessionTokens;
}
