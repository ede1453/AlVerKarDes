import { BACKEND_ORIGIN, IdentityUser, WatchlistItem } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";

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

async function fetchWatchlist(token: string, userId: string): Promise<WatchlistItem[] | null> {
  try {
    const res = await fetch(`${BACKEND_ORIGIN}/api/v1/watchlist/users/${userId}/items`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    const body = await res.json();
    // Real backend response shape is {"items": [...]}, not a bare array -
    // confirmed live (2026-07-19), differs from what was assumed in the task spec.
    if (!body || !Array.isArray(body.items)) return null;
    return body.items as WatchlistItem[];
  } catch {
    return null;
  }
}

export default async function WatchlistPage() {
  const token = await getSessionToken();
  const user = token ? await fetchMe(token) : null;

  if (!token || !user) {
    return (
      <div>
        <h1>Takip Listem</h1>
        <p className="error-box">
          Oturum bilgisi dogrulanamadi. Lutfen tekrar giris yapmayi deneyin.
        </p>
      </div>
    );
  }

  const items = await fetchWatchlist(token, user.id);

  return (
    <div>
      <h1>Takip Listem</h1>
      {items === null ? (
        <p className="error-box">
          Takip listesi alinirken bir hata olustu. Backend&apos;e ulasilamadi, lutfen daha sonra
          tekrar deneyin.
        </p>
      ) : items.length === 0 ? (
        <p className="notice-box">Henuz takip listende bir sey yok.</p>
      ) : (
        <ul>
          {items.map((item) => (
            <li key={item.id}>{JSON.stringify(item)}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
