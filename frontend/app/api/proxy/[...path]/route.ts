import { NextRequest, NextResponse } from "next/server";
import { BACKEND_ORIGIN } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";

// Catch-all proxy for AUTHENTICATED/OWNER_ONLY backend endpoints called from
// Client Components. Keeps the raw JWT server-side: the browser only ever
// talks to this same-origin route, never sees the token.
async function forward(request: NextRequest, path: string[]) {
  const token = await getSessionToken();
  if (!token) {
    return NextResponse.json({ detail: "not_authenticated" }, { status: 401 });
  }

  const targetPath = path.join("/");
  const search = request.nextUrl.search;
  const targetUrl = `${BACKEND_ORIGIN}/api/v1/${targetPath}${search}`;

  const init: RequestInit = {
    method: request.method,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    cache: "no-store",
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    const bodyText = await request.text();
    if (bodyText) {
      init.body = bodyText;
    }
  }

  let backendRes: Response;
  try {
    backendRes = await fetch(targetUrl, init);
  } catch {
    return NextResponse.json({ detail: "backend_unreachable" }, { status: 502 });
  }

  const contentType = backendRes.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const body = await backendRes.json().catch(() => null);
    return NextResponse.json(body, { status: backendRes.status });
  }

  const text = await backendRes.text();
  return new NextResponse(text, { status: backendRes.status });
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params;
  return forward(request, path);
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params;
  return forward(request, path);
}

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params;
  return forward(request, path);
}
