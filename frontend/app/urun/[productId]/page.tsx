import { notFound } from "next/navigation";
import { BACKEND_ORIGIN, ProductDetail } from "@/lib/backend";

interface ProductPageProps {
  params: Promise<{ productId: string }>;
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

export async function generateMetadata({ params }: ProductPageProps) {
  const { productId } = await params;
  const result = await fetchProductDetail(productId);
  if (result.kind !== "ok") {
    return { title: "Urun | AlVerKarDes" };
  }
  return { title: `${result.data.product.title} | AlVerKarDes` };
}

export default async function ProductPage({ params }: ProductPageProps) {
  const { productId } = await params;
  const result = await fetchProductDetail(productId);

  if (result.kind === "not_found") {
    notFound();
  }

  if (result.kind === "error") {
    return (
      <div>
        <p className="error-box">
          Urun bilgisi alinirken bir hata olustu. Backend&apos;e ulasilamadi, lutfen daha sonra
          tekrar deneyin.
        </p>
      </div>
    );
  }

  const { product, offers, price_history: priceHistory, deal_signal: dealSignal } = result.data;

  return (
    <div>
      <h1>{product.title}</h1>
      <p style={{ color: "#666" }}>{product.canonical_key}</p>

      <section style={{ marginTop: "1.5rem" }}>
        <h2>Teklifler</h2>
        {offers.length === 0 ? (
          <p className="notice-box">Bu urun icin henuz kayitli bir teklif yok.</p>
        ) : (
          <table className="offers-table">
            <thead>
              <tr>
                <th>Magaza</th>
                <th>Fiyat</th>
                <th>Stok</th>
                <th>Veri</th>
                <th>Link</th>
              </tr>
            </thead>
            <tbody>
              {offers.map((offer) => (
                <tr key={offer.offer_id}>
                  <td>{offer.store}</td>
                  <td>
                    {offer.price} {offer.currency}
                  </td>
                  <td>{offer.stock_status ?? "bilinmiyor"}</td>
                  <td>
                    <span className={`badge ${offer.is_real_data ? "badge-real" : "badge-unverified"}`}>
                      {offer.is_real_data ? "gercek veri" : "dogrulanmamis"}
                    </span>
                  </td>
                  <td>
                    <a href={offer.url} target="_blank" rel="noopener noreferrer">
                      goruntule
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section style={{ marginTop: "1.5rem" }}>
        <h2>Fiyat gecmisi</h2>
        {priceHistory.status === "OK" ? (
          <ul>
            <li>Guncel fiyat: {priceHistory.latest_price}</li>
            <li>En dusuk: {priceHistory.min_price}</li>
            <li>Ortalama: {priceHistory.average_price}</li>
            <li>En yuksek: {priceHistory.max_price}</li>
            <li>Trend: {priceHistory.trend}</li>
          </ul>
        ) : (
          <p className="notice-box">
            Bu urun icin henuz gercek fiyat gecmisi yok ({priceHistory.reason}).
          </p>
        )}
      </section>

      {dealSignal && (
        <section style={{ marginTop: "1.5rem" }}>
          <h2>Firsat sinyali</h2>
          <div className="deal-card">
            <p>
              <strong>Karar:</strong> {dealSignal.deal_score.decision} (skor {dealSignal.deal_score.score})
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
