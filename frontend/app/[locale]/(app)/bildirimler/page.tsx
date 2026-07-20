import type { Locale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { BACKEND_ORIGIN, IdentityUser, NotificationPreferences, Subscription } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";
import NotificationPreferencesForm from "@/components/NotificationPreferencesForm";

interface NotificationPreferencesPageProps {
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

async function fetchPreferences(
  token: string,
  userId: string
): Promise<NotificationPreferences | null> {
  try {
    const res = await fetch(`${BACKEND_ORIGIN}/api/v1/deal-notifications/preferences/${userId}`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as NotificationPreferences;
  } catch {
    return null;
  }
}

async function fetchSubscription(token: string, userId: string): Promise<Subscription | null> {
  try {
    const res = await fetch(`${BACKEND_ORIGIN}/api/v1/billing/subscription/${userId}`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as Subscription;
  } catch {
    return null;
  }
}

export default async function NotificationPreferencesPage({
  params,
}: NotificationPreferencesPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("notificationPreferences");
  // Session-error text is shared verbatim with the dashboard/watchlist pages
  // - sourced from the "dashboard" namespace so there's a single message
  // key, not a duplicated string across namespaces.
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

  const [preferences, subscription] = await Promise.all([
    fetchPreferences(token, user.id),
    fetchSubscription(token, user.id),
  ]);

  return (
    <div>
      <h1>{t("heading")}</h1>
      {preferences === null || subscription === null ? (
        <p className="error-box">{t("fetchError")}</p>
      ) : (
        <NotificationPreferencesForm
          userId={user.id}
          initialPreferences={preferences}
          isPremium={subscription.tier === "PREMIUM"}
        />
      )}
    </div>
  );
}
