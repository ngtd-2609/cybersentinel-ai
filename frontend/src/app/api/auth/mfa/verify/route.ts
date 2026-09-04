import { NextResponse } from "next/server";

import type { AuthUser } from "@/lib/auth";
import { BACKEND_API_URL } from "@/lib/server/backend";
import { setSessionCookies, type SessionTokens } from "@/lib/server/session";

export async function POST(request: Request) {
  const verification = await request.json().catch(() => null);
  if (!verification) {
    return NextResponse.json(
      { detail: "Invalid MFA verification request" },
      { status: 400 },
    );
  }

  const verifyResponse = await fetch(`${BACKEND_API_URL}/auth/mfa/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(verification),
    cache: "no-store",
  });
  if (!verifyResponse.ok) {
    const error = await verifyResponse.json().catch(() => ({
      detail: "Unable to verify authentication code",
    }));
    return NextResponse.json(error, { status: verifyResponse.status });
  }

  const token = (await verifyResponse.json()) as SessionTokens;
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
