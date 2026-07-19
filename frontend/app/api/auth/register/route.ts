import { NextRequest, NextResponse } from "next/server";
import { BACKEND_ORIGIN } from "@/lib/backend";

// Thin proxy to POST /api/v1/identity/register. No cookie involved - register
// doesn't return a token in this backend.
export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "invalid_json_body" }, { status: 400 });
  }

  let backendRes: Response;
  try {
    backendRes = await fetch(`${BACKEND_ORIGIN}/api/v1/identity/register`, {
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
