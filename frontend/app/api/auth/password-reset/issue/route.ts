import { NextRequest, NextResponse } from "next/server";
import { BACKEND_ORIGIN } from "@/lib/backend";

// Thin proxy to POST /api/v1/auth/password-reset/issue. PUBLIC, no auth.
// This endpoint is deliberately enumeration-safe on the backend (always
// 200 regardless of whether the identifier belongs to a real account) - no
// cookie/session logic needed here, we just forward body + status verbatim.
export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "invalid_json_body" }, { status: 400 });
  }

  let backendRes: Response;
  try {
    backendRes = await fetch(`${BACKEND_ORIGIN}/api/v1/auth/password-reset/issue`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ detail: "backend_unreachable" }, { status: 502 });
  }

  const backendBody = await backendRes.json().catch(() => ({}));
  return NextResponse.json(backendBody, { status: backendRes.status });
}
