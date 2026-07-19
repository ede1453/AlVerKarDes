import type { Locale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { BACKEND_ORIGIN, DealFeedResponse } from "@/lib/backend";

interface DealsPageProps {
  params: Promise<{ locale: Locale }>;
}

type FeedResult = { kind: "ok"; data: DealFeedResponse } | { kind: "error" };

async function fetchDealFeed(): Promise<FeedResult> {
  let res: Response;
  try {
    res = await fetch(`${BACKEND_ORIGIN}/api/v1/deal-feed/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ limit: 50 }),
      cache: "no-store",
    });
  } catch {
    return { kind: "error" };
  }
  if (!res.ok) {
    return { kind: "error" };
  }
  return { kind: "ok", data: (await res.json()) as DealFeedResponse };
}

export default async function DealsPage({ params }: DealsPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("deals");

  const result = await fetchDealFeed();

  return (
    <div>
      <h1>{t("heading")}</h1>

      {result.kind === "error" ? (
        <p className="error-box">{t("fetchError")}</p>
      ) : result.data.items.length === 0 ? (
        <p className="notice-box">{t("empty")}</p>
      ) : (
        <table className="offers-table">
          <thead>
            <tr>
              <th>{t("tableProduct")}</th>
              <th>{t("tableStore")}</th>
              <th>{t("tablePrice")}</th>
              <th>{t("tableDecision")}</th>
              <th>{t("tableScore")}</th>
            </tr>
          </thead>
          <tbody>
            {result.data.items.map((item) => {
              const decisionKey =
                item.deal_decision === "BUY" || item.deal_decision === "WATCH" || item.deal_decision === "SKIP"
                  ? item.deal_decision
                  : null;
              return (
                <tr key={item.offer_id}>
                  <td>
                    <Link href={`/urun/${item.product_id}`}>{item.product_name}</Link>
                  </td>
                  <td>{item.marketplace}</td>
                  <td>
                    {item.price} {item.currency}
                  </td>
                  <td>
                    {decisionKey ? (
                      <span className={`badge badge-decision-${decisionKey.toLowerCase()}`}>
                        {t(`decision.${decisionKey}`)}
                      </span>
                    ) : (
                      t("decision.unknown")
                    )}
                  </td>
                  <td>{item.personalized_score}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
