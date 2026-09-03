import { NextResponse } from "next/server";

import { AUTH_COOKIE_NAME, type AuthUser } from "@/lib/auth";
import {
  AUTH_COOKIE_OPTIONS,
  BACKEND_API_URL,
} from "@/lib/server/backend";

interface TokenResponse {
  access_token: string;
}

export async function POST(request: Request) {
  const credentials = await request.json().catch(() => null);

  if (!credentials) {
    return NextResponse.json(
      { detail: "Invalid login request" },
      { status: 400 },
    );
  }

  const loginResponse = await fetch(`${BACKEND_API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
    cache: "no-store",
  });

  if (!loginResponse.ok) {
    const error = await loginResponse.json().catch(() => ({
      detail: "Unable to sign in",
    }));
    return NextResponse.json(error, { status: loginResponse.status });
  }

  const token = (await loginResponse.json()) as TokenResponse;
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
  response.cookies.set(
    AUTH_COOKIE_NAME,
    token.access_token,
    AUTH_COOKIE_OPTIONS,
  );

  return response;
}
