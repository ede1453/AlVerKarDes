import Link from "next/link";
import { BACKEND_ORIGIN, ProductSearchResponse } from "@/lib/backend";

interface SearchPageProps {
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

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const { q } = await searchParams;
  const query = q?.trim() ?? "";
  const results = query ? await searchProducts(query) : null;

  return (
    <div>
      <h1>Urun ara</h1>
      <form action="/" method="get" style={{ display: "flex", gap: "0.5rem", maxWidth: 480 }}>
        <input
          type="text"
          name="q"
          defaultValue={query}
          placeholder="Urun adi..."
          aria-label="Urun ara"
          style={{ flex: 1, padding: "0.5rem", border: "1px solid #999", borderRadius: 4 }}
        />
        <button type="submit" className="btn">
          Ara
        </button>
      </form>

      {query && (
        <div style={{ marginTop: "1.5rem" }}>
          {results === null ? (
            <p className="error-box">
              Arama sirasinda bir hata olustu. Backend&apos;e ulasilamadi, lutfen daha sonra
              tekrar deneyin.
            </p>
          ) : results.items.length === 0 ? (
            <p className="notice-box">&quot;{query}&quot; icin sonuc bulunamadi.</p>
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
