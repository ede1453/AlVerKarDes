import { notFound } from "next/navigation";
import type { Locale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { BACKEND_ORIGIN, IdentityUser, ProductDetail } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";
import AddToWatchlistButton from "@/components/AddToWatchlistButton";

interface ProductPageProps {
  params: Promise<{ locale: Locale; productId: string }>;
}

type DetailResult =
  | { kind: "ok"; data: ProductDetail }
  | { kind: "not_found" }
  | { kind: "error" };

async function fetchProductDetail(productId: string): Promise<DetailResult> {
  let res: Response;
  try {
    res = await fetch(`${BACKEND_ORIGIN}/api/v1/products/${productId}/detail`, {
      cache: "no-store",
    });
  } catch {
    return { kind: "error" };
  }

  if (res.status === 404) {
    return { kind: "not_found" };
  }
  if (!res.ok) {
    return { kind: "error" };
  }
  return { kind: "ok", data: (await res.json()) as ProductDetail };
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

export async function generateMetadata({ params }: ProductPageProps) {
  const { locale, productId } = await params;
  const t = await getTranslations({ locale, namespace: "productDetail" });
  const result = await fetchProductDetail(productId);
  if (result.kind !== "ok") {
    return { title: t("metaFallbackTitle") };
  }
  return { title: t("metaTitle", { title: result.data.product.title }) };
}

export default async function ProductPage({ params }: ProductPageProps) {
  const { locale, productId } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("productDetail");
  const result = await fetchProductDetail(productId);

  if (result.kind === "not_found") {
    notFound();
  }

  if (result.kind === "error") {
    return (
      <div>
        <p className="error-box">{t("fetchError")}</p>
      </div>
    );
  }

  const { product, offers, price_history: priceHistory, deal_signal: dealSignal } = result.data;

  const token = await getSessionToken();
  const user = token ? await fetchMe(token) : null;

  return (
    <div>
      <h1>{product.title}</h1>
      <p style={{ color: "#666" }}>{product.canonical_key}</p>

      {user ? (
        <AddToWatchlistButton userId={user.id} productKey={product.canonical_key} query={product.title} />
      ) : (
        <p className="notice-box">{t("watchlistLoginPrompt")}</p>
      )}

      <section style={{ marginTop: "1.5rem" }}>
        <h2>{t("offersHeading")}</h2>
        {offers.length === 0 ? (
          <p className="notice-box">{t("noOffers")}</p>
        ) : (
          <table className="offers-table">
            <thead>
              <tr>
                <th>{t("tableStore")}</th>
                <th>{t("tablePrice")}</th>
                <th>{t("tableStock")}</th>
                <th>{t("tableData")}</th>
                <th>{t("tableLink")}</th>
              </tr>
            </thead>
            <tbody>
              {offers.map((offer) => (
                <tr key={offer.offer_id}>
                  <td>{offer.store}</td>
                  <td>
                    {offer.price} {offer.currency}
                  </td>
                  <td>{offer.stock_status ?? t("stockUnknown")}</td>
                  <td>
                    <span className={`badge ${offer.is_real_data ? "badge-real" : "badge-unverified"}`}>
                      {offer.is_real_data ? t("badgeReal") : t("badgeUnverified")}
                    </span>
                  </td>
                  <td>
                    <a href={offer.url} target="_blank" rel="noopener noreferrer">
                      {t("viewLink")}
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section style={{ marginTop: "1.5rem" }}>
        <h2>{t("priceHistoryHeading")}</h2>
        {priceHistory.status === "OK" ? (
          <ul>
            <li>
              {t("currentPrice")} {priceHistory.latest_price}
            </li>
            <li>
              {t("minPrice")} {priceHistory.min_price}
            </li>
            <li>
              {t("avgPrice")} {priceHistory.average_price}
            </li>
            <li>
              {t("maxPrice")} {priceHistory.max_price}
            </li>
            <li>
              {t("trendLabel")} {priceHistory.trend}
            </li>
          </ul>
        ) : (
          <p className="notice-box">{t("noHistory", { reason: priceHistory.reason })}</p>
        )}
      </section>

      {dealSignal && (
        <section style={{ marginTop: "1.5rem" }}>
          <h2>{t("dealSignalHeading")}</h2>
          <div className="deal-card">
            <p>
              <strong>{t("decision")}</strong> {dealSignal.deal_score.decision}{" "}
              {t("scoreLabel", { score: dealSignal.deal_score.score })}
            </p>
            <p>{dealSignal.message}</p>
            {dealSignal.deal_score.reasons.length > 0 && (
              <ul>
                {dealSignal.deal_score.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
