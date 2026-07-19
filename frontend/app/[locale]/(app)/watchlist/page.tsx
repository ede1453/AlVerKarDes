import type { Locale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { BACKEND_ORIGIN, IdentityUser, WatchlistItem } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";

interface WatchlistPageProps {
  // The (app)/layout.tsx guard above already validates this against
  // routing.locales (notFound() otherwise), so it's safe to type as Locale here.
  params: Promise<{ locale: Locale }>;
}

async function fetchMe(token: string): Promise<IdentityUser | null> {
  try {
    const res = await fetch(`${BACKEND_ORIGIN}/api/v1/identity/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as IdentityUser;
  } catch {
    return null;
  }
}

async function fetchWatchlist(token: string, userId: string): Promise<WatchlistItem[] | null> {
  try {
    const res = await fetch(`${BACKEND_ORIGIN}/api/v1/watchlist/users/${userId}/items`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    const body = await res.json();
    // Real backend response shape is {"items": [...]}, not a bare array -
    // confirmed live (2026-07-19), differs from what was assumed in the task spec.
    if (!body || !Array.isArray(body.items)) return null;
    return body.items as WatchlistItem[];
  } catch {
    return null;
  }
}

export default async function WatchlistPage({ params }: WatchlistPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("watchlist");
  // Session-error text is shared verbatim with the dashboard page - sourced
  // from the "dashboard" namespace so there's a single message key, not a
  // duplicated string across namespaces.
  const tDashboard = await getTranslations("dashboard");

  const token = await getSessionToken();
  const user = token ? await fetchMe(token) : null;

  if (!token || !user) {
    return (
      <div>
        <h1>{t("heading")}</h1>
        <p className="error-box">{tDashboard("sessionError")}</p>
      </div>
    );
  }

  const items = await fetchWatchlist(token, user.id);

  return (
    <div>
      <h1>{t("heading")}</h1>
      {items === null ? (
        <p className="error-box">{t("fetchError")}</p>
      ) : items.length === 0 ? (
        <p className="notice-box">{t("empty")}</p>
      ) : (
        <ul>
          {items.map((item) => (
            <li key={item.id}>{JSON.stringify(item)}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
