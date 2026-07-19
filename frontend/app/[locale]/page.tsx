import type { Locale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { BACKEND_ORIGIN, ProductSearchResponse } from "@/lib/backend";

interface SearchPageProps {
  params: Promise<{ locale: Locale }>;
  searchParams: Promise<{ q?: string }>;
}

async function searchProducts(q: string): Promise<ProductSearchResponse | null> {
  try {
    const res = await fetch(
      `${BACKEND_ORIGIN}/api/v1/products/search?q=${encodeURIComponent(q)}&limit=20`,
      { cache: "no-store" }
    );
    if (!res.ok) {
      return null;
    }
    return (await res.json()) as ProductSearchResponse;
  } catch {
    return null;
  }
}

export default async function SearchPage({ params, searchParams }: SearchPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("search");

  const { q } = await searchParams;
  const query = q?.trim() ?? "";
  const results = query ? await searchProducts(query) : null;

  return (
    <div>
      <h1>{t("title")}</h1>
      <form
        action={`/${locale}`}
        method="get"
        style={{ display: "flex", gap: "0.5rem", maxWidth: 480 }}
      >
        <input
          type="text"
          name="q"
          defaultValue={query}
          placeholder={t("placeholder")}
          aria-label={t("ariaLabel")}
          style={{ flex: 1, padding: "0.5rem", border: "1px solid #999", borderRadius: 4 }}
        />
        <button type="submit" className="btn">
          {t("button")}
        </button>
      </form>

      {query && (
        <div style={{ marginTop: "1.5rem" }}>
          {results === null ? (
            <p className="error-box">{t("error")}</p>
          ) : results.items.length === 0 ? (
            <p className="notice-box">{t("noResults", { query })}</p>
          ) : (
            <ul>
              {results.items.map((item) => (
                <li key={item.id} style={{ marginBottom: "0.5rem" }}>
                  <Link href={`/urun/${item.id}`}>{item.title}</Link>
                  <div style={{ fontSize: "0.85rem", color: "#666" }}>{item.canonical_key}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
