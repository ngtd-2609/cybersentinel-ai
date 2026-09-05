import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { AUTH_COOKIE_NAME } from "@/lib/auth";
import { BACKEND_API_URL } from "@/lib/server/backend";

export async function GET(request: Request) {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const backendResponse = await fetch(`${BACKEND_API_URL}/stream/soc`, {
    headers: {
      Accept: "text/event-stream",
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
    signal: request.signal,
  });
  if (!backendResponse.ok || !backendResponse.body) {
    return NextResponse.json(
      { detail: "Real-time stream unavailable" },
      { status: backendResponse.status },
    );
  }

  return new Response(backendResponse.body, {
    status: 200,
    headers: {
      "Cache-Control": "no-cache, no-transform",
      "Content-Type": "text/event-stream",
      "X-Accel-Buffering": "no",
    },
  });
}
