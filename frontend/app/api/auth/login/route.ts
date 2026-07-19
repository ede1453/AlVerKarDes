import { NextRequest, NextResponse } from "next/server";
import { BACKEND_ORIGIN, SESSION_COOKIE_NAME } from "@/lib/backend";

export async function POST(request: NextRequest) {
  let body: { email?: string; password?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "invalid_json_body" }, { status: 400 });
  }

  const { email, password } = body;
  if (!email || !password) {
    return NextResponse.json({ detail: "email_and_password_required" }, { status: 400 });
  }

  let backendRes: Response;
  try {
    backendRes = await fetch(`${BACKEND_ORIGIN}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier: email, password }),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ detail: "backend_unreachable" }, { status: 502 });
  }

  const backendBody = await backendRes.json().catch(() => ({}));

  if (!backendRes.ok) {
    // Forward the backend's real status/error, do not mask it with a generic message.
    return NextResponse.json(backendBody, { status: backendRes.status });
  }

  const accessToken = backendBody?.access_token as string | undefined;
  if (!accessToken) {
    return NextResponse.json({ detail: "login_response_missing_access_token" }, { status: 502 });
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.set({
    name: SESSION_COOKIE_NAME,
    value: accessToken,
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    secure: process.env.NODE_ENV === "production",
  });
  return response;
}
