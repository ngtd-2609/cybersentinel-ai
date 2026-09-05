import { NextResponse } from "next/server";

import { BACKEND_API_URL } from "@/lib/server/backend";

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_API_URL}/ready`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok) {
      return NextResponse.json({ status: "waking" }, { status: 503 });
    }
    return NextResponse.json({ status: "ready" });
  } catch {
    return NextResponse.json({ status: "waking" }, { status: 503 });
  }
}
