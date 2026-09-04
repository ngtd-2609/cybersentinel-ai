import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { AUTH_COOKIE_NAME, REFRESH_COOKIE_NAME } from "@/lib/auth";
import { BACKEND_API_URL } from "@/lib/server/backend";
import {
  clearSessionCookies,
  refreshSession,
  setSessionCookies,
  type SessionTokens,
} from "@/lib/server/session";

export async function GET() {
  const cookieStore = await cookies();
  let token = cookieStore.get(AUTH_COOKIE_NAME)?.value;
  const refreshToken = cookieStore.get(REFRESH_COOKIE_NAME)?.value;

  if (!token) {
    return NextResponse.json(
      { detail: "Not authenticated" },
      { status: 401 },
    );
  }

  const loadUser = (accessToken: string) =>
    fetch(`${BACKEND_API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });

  let refreshed: SessionTokens | null = null;
  let backendResponse = await loadUser(token);
  if (backendResponse.status === 401 && refreshToken) {
    refreshed = await refreshSession(refreshToken);
    if (refreshed) {
      token = refreshed.access_token;
      backendResponse = await loadUser(token);
    }
  }
  const body = await backendResponse.arrayBuffer();
  const response = new NextResponse(body, {
    status: backendResponse.status,
    headers: {
      "Content-Type":
        backendResponse.headers.get("Content-Type") ?? "application/json",
    },
  });

  if (refreshed) {
    setSessionCookies(response, refreshed);
  }
  if (backendResponse.status === 401 || backendResponse.status === 403) {
    clearSessionCookies(response);
  }

  return response;
}
