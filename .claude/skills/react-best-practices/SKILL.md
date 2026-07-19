---
name: react-best-practices
description: "Next.js (App Router) + React best practices for hybrid SSR/CSR products — server-rendered public pages for SEO, client-rendered authenticated pages for personalized data. Written for AlVerKarDes CLIENT-002 (Next.js, web-first)."
risk: unknown
source: authored
date_added: "2026-07-19"
---

## Use this skill when

- Building or reviewing Next.js/React code in `AlVerKarDes/frontend/` (CLIENT-002+).
- Deciding whether a page/component should be a Server Component (SSR) or a
  Client Component (CSR).
- Wiring authenticated (JWT-bearing) data fetches from the browser to the
  FastAPI backend.
- Reviewing a PR that touches routing, data-fetching, or auth state in the
  frontend.

## Do not use this skill when

- The task is purely backend (FastAPI/SQLAlchemy) — use `fastapi-pro`/`postgresql` instead.
- The task is about the CLIENT-001 static verification tool (`web/`) — that
  deliberately has no framework, no build step; do not migrate it here without
  a separate, approved item.

## Instructions

1. Before writing a page, classify it: **PUBLIC/SSR** (no user identity
   needed, benefits from indexing) or **AUTHENTICATED/CSR** (personal data,
   no SEO value). See `[[../../../05-Decisions/ADR-011-CLIENT-002a-Kapsam-Iskelet-Plani]]`
   in WIKI_ROOT for the concrete page-by-page split already agreed for this
   project — don't re-derive it from scratch, extend it.
2. Default new data-fetching code to Server Components (`async function Page()`
   fetching directly) unless the data is user-specific or requires
   interactivity (forms, buttons with client state).
3. Never put a JWT in a cookie without `httpOnly`+`secure`+`sameSite`; never
   read `localStorage` tokens inside a Server Component (it has no access to
   browser storage — this is a common hybrid-rendering mistake).
4. Keep the API base URL same-origin from the browser's perspective (Next.js
   `rewrites()` proxy to the FastAPI backend) — this project hit a real CORS
   config gap once (ADR-010) and deliberately avoided it in CLIENT-001 by
   serving same-origin. Don't reintroduce cross-origin fetches without a
   reason.
5. Real verification means a real browser tab against a real running Next.js
   dev server + real FastAPI backend — not a component snapshot test alone.

## Core Concepts

### 1. Server Components vs Client Components (App Router)

| | Server Component (default) | Client Component (`"use client"`) |
|---|---|---|
| Runs | On the server (or at build time) | In the browser |
| Can fetch data directly | Yes (`await fetch(...)` in the component) | No — needs `useEffect`/a hook/a server action |
| Can use `useState`/`useEffect`/event handlers | No | Yes |
| Ships JS to the browser | No (zero bundle cost) | Yes |
| SEO-visible on first paint | Yes | Only after hydration (bad for crawlers that don't run JS) |

**Rule of thumb for this project:** product detail pages, deal-feed listing
pages, and search-result pages are Server Components that call the
FastAPI PUBLIC endpoints directly (server-to-server, no CORS, no token).
Login/register forms, the dashboard, watchlist, alert rules, and any
"run the full AI pipeline" action are Client Components because they need
either browser-side interactivity or a bearer token that only exists in the
browser session.

### 2. Data fetching split

- **SSR (Server Component)**: `fetch()` the FastAPI PUBLIC endpoint directly
  from the Next.js server process. Use `next: { revalidate: N }` for
  cacheable catalog/price data instead of `cache: "no-store"` everywhere —
  price history doesn't change every second, don't defeat caching by default.
- **CSR (Client Component)**: fetch AUTHENTICATED/OWNER_ONLY endpoints from
  the browser with `Authorization: Bearer <token>`, using a small fetch
  wrapper that centralizes 401-handling (redirect to login) — don't
  duplicate auth-header logic per component.
- Never call an OWNER_ONLY/AUTHENTICATED endpoint from a Server Component
  using a token pulled from a cookie unless that cookie is itself
  `httpOnly` and set by a server action/route handler — a token accessible
  to client JS defeats the point of `httpOnly`, and a token read from a
  non-httpOnly cookie in a Server Component means client JS could have read
  it too.

### 3. Auth state without a global client-side store

For a small app (this project's stated "küçük başlıyoruz" principle),
prefer:
- A `httpOnly` session cookie set by a Next.js Route Handler that proxies
  `POST /api/v1/auth/login` (the Route Handler talks to FastAPI, gets the
  JWT, sets it as `httpOnly` cookie — the browser's JS never touches the
  raw token).
- Server Components read the cookie via `cookies()` to decide
  logged-in-vs-not for layout purposes (e.g. show "Giriş Yap" vs "Hesabım").
- Client Components that need the token for a `fetch()` call it through a
  Route Handler proxy (`/api/proxy/...`) rather than reading the cookie
  directly — keeps the raw JWT server-side only.

Only reach for a client-state library (Zustand/Redux/Context) if multiple
unrelated client components need to react to auth changes without a page
reload — don't add one preemptively (YAGNI, matches this project's existing
discipline against premature abstraction).

### 4. Routing conventions (App Router)

```
app/
  (public)/
    page.tsx                  # ana sayfa / arama
    urun/[canonicalKey]/page.tsx   # SSR ürün detay
    firsatlar/page.tsx        # SSR fırsat/deal feed
    giris/page.tsx            # login (client form)
    kayit/page.tsx            # register (client form)
  (app)/                      # route group, tümü authenticated
    layout.tsx                # auth guard burada (redirect if no session)
    dashboard/page.tsx
    watchlist/page.tsx
    uyarilar/page.tsx
    karar-gecmisi/page.tsx
  api/
    proxy/[...path]/route.ts  # FastAPI'ye same-origin proxy
```

Route groups (`(public)`, `(app)`) don't affect the URL — they let you put a
shared authenticated layout (with the redirect-if-logged-out guard) around
exactly the pages that need it, without polluting public page URLs with a
prefix.

### 5. Testing

- Component/unit tests: React Testing Library, query by role/label not by
  CSS class or test-id where possible (accessibility side-effect).
- End-to-end: a real browser against a real dev server (Playwright, or this
  project's existing `mcp__Claude_Browser__*` tooling for manual/agent-driven
  verification) — this project has already hit one bug (CSP silently
  blocking `<script>` tags in CLIENT-001) that only a real browser caught,
  not curl or a component test. Don't skip real-browser verification for
  auth flows or anything touching CSP/CORS/cookies.
- Negative controls apply here too: when fixing an auth-guard bug, revert it
  temporarily, prove the bug reproduces in a real browser, then restore —
  same discipline as the backend work in this project.

### 6. Performance/SEO checklist for public pages

- Use `generateMetadata()` for per-product `<title>`/`<meta description>` —
  don't leave every page with the same static title.
- Use `next/image` for any product imagery once that exists (not yet in
  scope) — don't hand-roll `<img>` with no size hints.
- Avoid `"use client"` at the top of a whole page just because one small
  widget needs interactivity — push `"use client"` down to the smallest
  leaf component (e.g. a "watchlist'e ekle" button), keep the page shell a
  Server Component so the surrounding content stays crawlable.

## Anti-patterns to flag in review

- A Server Component that reads `localStorage` or `window` — will crash at
  build/render time, not just "not work."
- `"use client"` on a page whose only job is to display server-fetched data
  with no interactivity — unnecessary bundle cost, unnecessary SEO loss.
- A raw JWT stored in `localStorage` and attached to `fetch` calls from
  multiple components with copy-pasted header logic.
- Cross-origin `fetch("https://api.alverkardes...")` calls from the browser
  when a same-origin Route Handler proxy would avoid CORS entirely (this
  project's own CLIENT-000/001 history: CORS config was found broken once,
  same-origin serving was the fix that sidestepped it).
- A public/SSR page that silently swallows a FastAPI error and renders a
  fabricated/default value instead of an honest "veri yok" state — matches
  this project's zero-tolerance stance on fabricated data (CLIENT-000b,
  CONNECT-001, CONNECT-005 were all real bugs of exactly this shape on the
  backend; don't reintroduce the same failure mode in the frontend).
