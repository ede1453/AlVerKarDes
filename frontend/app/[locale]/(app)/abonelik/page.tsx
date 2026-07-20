import type { Locale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { BACKEND_ORIGIN, IdentityUser, Plan, Subscription } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";
import PlanUpgradeButton from "@/components/PlanUpgradeButton";

interface BillingPageProps {
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

async function fetchPlans(): Promise<Plan[] | null> {
  // PUBLIC endpoint - no token needed, but this page itself sits behind the
  // (app) route-group auth guard already.
  try {
    const res = await fetch(`${BACKEND_ORIGIN}/api/v1/billing/plans`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    const body = await res.json();
    if (!body || !Array.isArray(body.plans)) return null;
    return body.plans as Plan[];
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

export default async function BillingPage({ params }: BillingPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("billing");
  // Session-error text is shared verbatim with the dashboard/watchlist/
  // bildirimler/profil pages - sourced from the "dashboard" namespace so
  // there's a single message key, not a duplicated string across namespaces.
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

  const [plans, subscription] = await Promise.all([
    fetchPlans(),
    fetchSubscription(token, user.id),
  ]);

  if (plans === null || subscription === null) {
    return (
      <div>
        <h1>{t("heading")}</h1>
        <p className="error-box">{t("fetchError")}</p>
      </div>
    );
  }

  const freePlan = plans.find((plan) => plan.tier === "FREE") ?? null;
  const premiumPlan = plans.find((plan) => plan.tier === "PREMIUM") ?? null;

  function formatWatchlistLimit(plan: Plan | null): string {
    if (!plan) return t("unknown");
    return plan.watchlist_limit === null
      ? t("unlimited")
      : t("watchlistLimitValue", { limit: plan.watchlist_limit });
  }

  function formatThresholdCustomization(plan: Plan | null): string {
    if (!plan) return t("unknown");
    return plan.threshold_customization ? t("thresholdCustomYes") : t("thresholdCustomNo");
  }

  return (
    <div>
      <h1>{t("heading")}</h1>
      <p>
        <strong>{t("currentPlanLabel")}</strong>{" "}
        {subscription.tier === "PREMIUM" ? t("tierPremium") : t("tierFree")}
      </p>

      <table className="offers-table" style={{ marginTop: "1rem" }}>
        <thead>
          <tr>
            <th>{t("tableFeature")}</th>
            <th
              className={subscription.tier === "FREE" ? "badge badge-real" : undefined}
            >
              {t("tierFree")}
              {subscription.tier === "FREE" ? ` (${t("currentPlanBadge")})` : ""}
            </th>
            <th
              className={subscription.tier === "PREMIUM" ? "badge badge-real" : undefined}
            >
              {t("tierPremium")}
              {subscription.tier === "PREMIUM" ? ` (${t("currentPlanBadge")})` : ""}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{t("featureWatchlistLimit")}</td>
            <td>{formatWatchlistLimit(freePlan)}</td>
            <td>{formatWatchlistLimit(premiumPlan)}</td>
          </tr>
          <tr>
            <td>{t("featureThresholdCustomization")}</td>
            <td>{formatThresholdCustomization(freePlan)}</td>
            <td>{formatThresholdCustomization(premiumPlan)}</td>
          </tr>
        </tbody>
      </table>

      <p className="field-note" style={{ marginTop: "1rem" }}>
        {t("mockDisclaimer")}
      </p>

      <PlanUpgradeButton userId={user.id} initialSubscription={subscription} />
    </div>
  );
}
