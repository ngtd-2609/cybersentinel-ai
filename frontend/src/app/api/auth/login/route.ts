import { NextResponse } from "next/server";

import type { AuthUser } from "@/lib/auth";
import { BACKEND_API_URL } from "@/lib/server/backend";
import {
  setSessionCookies,
  type SessionTokens,
} from "@/lib/server/session";

export async function POST(request: Request) {
  const credentials = await request.json().catch(() => null);

  if (!credentials) {
    return NextResponse.json(
      { detail: "Invalid login request" },
      { status: 400 },
    );
  }

  const loginHeaders = new Headers({ "Content-Type": "application/json" });
  const forwardedFor = request.headers.get("X-Forwarded-For");
  if (forwardedFor) {
    loginHeaders.set("X-Forwarded-For", forwardedFor);
  }

  const loginResponse = await fetch(`${BACKEND_API_URL}/auth/login`, {
    method: "POST",
    headers: loginHeaders,
    body: JSON.stringify(credentials),
    cache: "no-store",
  });

  if (!loginResponse.ok) {
    const error = await loginResponse.json().catch(() => ({
      detail: "Unable to sign in",
    }));
    return NextResponse.json(error, { status: loginResponse.status });
  }

  const token = (await loginResponse.json()) as SessionTokens;
  const userResponse = await fetch(`${BACKEND_API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token.access_token}` },
    cache: "no-store",
  });

  if (!userResponse.ok) {
    return NextResponse.json(
      { detail: "Unable to load the signed-in user" },
      { status: userResponse.status },
    );
  }

  const user = (await userResponse.json()) as AuthUser;
  const response = NextResponse.json(user);
  setSessionCookies(response, token);

  return response;
}
