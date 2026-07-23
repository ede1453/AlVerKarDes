import type { Locale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { BACKEND_ORIGIN, DealFeedResponse } from "@/lib/backend";

interface DealsPageProps {
  params: Promise<{ locale: Locale }>;
}

type FeedResult = { kind: "ok"; data: DealFeedResponse } | { kind: "error" };

// Mirrors the codes UserPreferenceScorer (app/domains/deal_feed/service.py)
// actually emits into personalization_reasons -- a fixed, known set, not
// arbitrary strings, so this narrows for next-intl's compile-time key
// checking. Any future backend code not in this list falls back to the raw
// code (see reasonLabel below) instead of a type error.
const KNOWN_REASON_CODES = [
  "PREFERRED_CATEGORY",
  "PREFERRED_BRAND",
  "BLOCKED_SOURCE",
  "ABOVE_MAXIMUM_PRICE",
  "DISCOUNT_THRESHOLD_MET",
] as const;
type KnownReasonCode = (typeof KNOWN_REASON_CODES)[number];

function isKnownReasonCode(code: string): code is KnownReasonCode {
  return (KNOWN_REASON_CODES as readonly string[]).includes(code);
}

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
              <th>{t("tableMessage")}</th>
              <th>{t("tableReasons")}</th>
            </tr>
          </thead>
          <tbody>
            {result.data.items.map((item) => {
              const decisionKey =
                item.deal_decision === "BUY" || item.deal_decision === "WATCH" || item.deal_decision === "SKIP"
                  ? item.deal_decision
                  : null;
              // The backend's decision engine (app/domains/deals/deal_score_engine.py)
              // only ever produces BUY/WATCH/WAIT, so "message" is keyed on the same
              // decisionKey logic as the badge above (falls back to "unknown" for the
              // same untranslatable values, e.g. WAIT -- a pre-existing mismatch with
              // this page's own BUY/WATCH/SKIP check, not something this i18n pass fixes).
              const messageKey = decisionKey ?? "unknown";
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
                  <td>{t(`message.${messageKey}`)}</td>
                  <td>
                    {item.personalization_reasons.length === 0
                      ? null
                      : item.personalization_reasons.map((reasonCode) => (
                          <span key={reasonCode} className="badge badge-reason">
                            {isKnownReasonCode(reasonCode) ? t(`reasons.${reasonCode}`) : reasonCode}
                          </span>
                        ))}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
