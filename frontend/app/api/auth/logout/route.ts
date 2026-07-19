import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME } from "@/lib/backend";

export async function POST(request: NextRequest) {
  // 303 (not the default 307) - a POST->307 redirect keeps the POST method,
  // and "/" has no POST handler, which 500s. 303 forces the browser to GET.
  const response = NextResponse.redirect(new URL("/", request.url), 303);
  response.cookies.delete(SESSION_COOKIE_NAME);
  return response;
}
