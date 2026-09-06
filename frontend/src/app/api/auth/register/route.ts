import { NextResponse } from "next/server";

import type { AuthUser } from "@/lib/auth";
import { BACKEND_API_URL } from "@/lib/server/backend";
import { setSessionCookies, type SessionTokens } from "@/lib/server/session";

function requestHeaders(request: Request) {
  const headers = new Headers({ "Content-Type": "application/json" });
  const forwardedFor = request.headers.get("X-Forwarded-For");
  if (forwardedFor) headers.set("X-Forwarded-For", forwardedFor);
  return headers;
}

export async function POST(request: Request) {
  const payload = await request.json().catch(() => null);
  if (!payload) {
    return NextResponse.json({ detail: "Invalid registration request" }, { status: 400 });
  }

  const headers = requestHeaders(request);
  const registration = await fetch(`${BACKEND_API_URL}/auth/register`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      email: payload.email,
      username: payload.username,
      full_name: payload.full_name || null,
      password: payload.password,
    }),
    cache: "no-store",
  });
  if (!registration.ok) {
    const error = await registration.json().catch(() => ({ detail: "Unable to create account" }));
    return NextResponse.json(error, { status: registration.status });
  }

  const login = await fetch(`${BACKEND_API_URL}/auth/login`, {
    method: "POST",
    headers,
    body: JSON.stringify({ email: payload.email, password: payload.password }),
    cache: "no-store",
  });
  if (!login.ok) {
    return NextResponse.json(
      { detail: "Account created. Please sign in." },
      { status: 201 },
    );
  }

  const token = (await login.json()) as SessionTokens;
  const userResponse = await fetch(`${BACKEND_API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token.access_token}` },
    cache: "no-store",
  });
  if (!userResponse.ok) {
    return NextResponse.json({ detail: "Account created. Please sign in." }, { status: 201 });
  }

  const response = NextResponse.json((await userResponse.json()) as AuthUser, { status: 201 });
  setSessionCookies(response, token);
  return response;
}
