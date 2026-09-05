import { NextResponse } from "next/server";

import type { AuthUser } from "@/lib/auth";
import { BACKEND_API_URL } from "@/lib/server/backend";
import { setSessionCookies, type SessionTokens } from "@/lib/server/session";

export async function POST() {
  if (process.env.NEXT_PUBLIC_DEMO_LOGIN_ENABLED !== "true") {
    return NextResponse.json({ detail: "Demo login is disabled" }, { status: 404 });
  }

  const email = process.env.CYBERSENTINEL_DEMO_EMAIL;
  const password = process.env.CYBERSENTINEL_DEMO_PASSWORD;
  if (!email || !password) {
    return NextResponse.json(
      { detail: "Demo login is not configured" },
      { status: 503 },
    );
  }

  try {
    const loginResponse = await fetch(`${BACKEND_API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      cache: "no-store",
      signal: AbortSignal.timeout(15000),
    });
    if (!loginResponse.ok) {
      return NextResponse.json(
        { detail: "Demo account is temporarily unavailable" },
        { status: loginResponse.status },
      );
    }

    const token = (await loginResponse.json()) as SessionTokens;
    const userResponse = await fetch(`${BACKEND_API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token.access_token}` },
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });
    if (!userResponse.ok) {
      return NextResponse.json(
        { detail: "Unable to load the demo account" },
        { status: userResponse.status },
      );
    }

    const user = (await userResponse.json()) as AuthUser;
    if (user.role === "ADMIN") {
      return NextResponse.json(
        { detail: "Unsafe demo account configuration" },
        { status: 503 },
      );
    }
    const response = NextResponse.json(user);
    setSessionCookies(response, token);
    return response;
  } catch {
    return NextResponse.json(
      { detail: "Demo services are still waking up" },
      { status: 503 },
    );
  }
}
