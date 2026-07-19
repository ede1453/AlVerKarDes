import type { Locale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { BACKEND_ORIGIN, IdentityUser } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";

interface DashboardPageProps {
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
    if (!res.ok) {
      return null;
    }
    return (await res.json()) as IdentityUser;
  } catch {
    return null;
  }
}

export default async function DashboardPage({ params }: DashboardPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("dashboard");

  // Layout guard already redirected to /giris if there's no cookie, but the
  // token can still be stale/invalid (e.g. expired) - handle that honestly.
  const token = await getSessionToken();
  const user = token ? await fetchMe(token) : null;

  if (!user) {
    return (
      <div>
        <h1>{t("heading")}</h1>
        <p className="error-box">{t("sessionError")}</p>
      </div>
    );
  }

  return (
    <div>
      <h1>{t("heading")}</h1>
      <p>
        <strong>{t("emailLabel")}</strong> {user.email}
      </p>
      <p>
        <strong>{t("displayNameLabel")}</strong> {user.display_name ?? t("notSpecified")}
      </p>
    </div>
  );
}
