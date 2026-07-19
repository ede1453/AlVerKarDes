import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

export default createMiddleware(routing);

export const config = {
  // Match every path except: /api/*, Next.js internals, and files with an
  // extension (static assets, favicon.ico, etc). This keeps the existing
  // Route Handlers (app/api/auth/*, app/api/proxy/*) untouched - they are
  // not pages and must never get a /de or /en prefix.
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
