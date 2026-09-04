import { cookies } from "next/headers";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { AUTH_COOKIE_NAME, REFRESH_COOKIE_NAME } from "@/lib/auth";
import { BACKEND_API_URL } from "@/lib/server/backend";
import {
  clearSessionCookies,
  refreshSession,
  setSessionCookies,
  type SessionTokens,
} from "@/lib/server/session";

interface RouteContext {
  params: Promise<{ path: string[] }>;
}

async function proxyRequest(
  request: NextRequest,
  context: RouteContext,
) {
  const cookieStore = await cookies();
  let token = cookieStore.get(AUTH_COOKIE_NAME)?.value;
  const refreshToken = cookieStore.get(REFRESH_COOKIE_NAME)?.value;

  if (!token) {
    return NextResponse.json(
      { detail: "Not authenticated" },
      { status: 401 },
    );
  }

  const { path } = await context.params;
  const target = new URL(
    `${BACKEND_API_URL}/${path.map(encodeURIComponent).join("/")}`,
  );
  target.search = request.nextUrl.search;

  const hasBody = !["GET", "HEAD"].includes(request.method);
  const requestBody = hasBody ? await request.arrayBuffer() : undefined;
  const forward = (accessToken: string) => {
    const headers = new Headers();
    headers.set("Authorization", `Bearer ${accessToken}`);
    headers.set("Accept", request.headers.get("Accept") ?? "application/json");

    const contentType = request.headers.get("Content-Type");
    if (contentType) {
      headers.set("Content-Type", contentType);
    }

    return fetch(target, {
      method: request.method,
      headers,
      body: requestBody,
      cache: "no-store",
    });
  };

  let refreshed: SessionTokens | null = null;
  let backendResponse = await forward(token);
  if (backendResponse.status === 401 && refreshToken) {
    refreshed = await refreshSession(refreshToken);
    if (refreshed) {
      token = refreshed.access_token;
      backendResponse = await forward(token);
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
  if (backendResponse.status === 401) {
    clearSessionCookies(response);
  }

  return response;
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
