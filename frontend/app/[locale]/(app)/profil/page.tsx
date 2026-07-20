import type { Locale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { BACKEND_ORIGIN, IdentityUser } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";
import ProfileForm from "@/components/ProfileForm";

interface ProfilePageProps {
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

export default async function ProfilePage({ params }: ProfilePageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("profile");
  // Session-error text is shared verbatim with the dashboard/watchlist/
  // bildirimler pages - sourced from the "dashboard" namespace so there's a
  // single message key, not a duplicated string across namespaces.
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

  return (
    <div>
      <h1>{t("heading")}</h1>
      <p>
        <strong>{t("emailLabel")}</strong> {user.email}
      </p>
      <ProfileForm userId={user.id} initialUser={user} />
    </div>
  );
}
