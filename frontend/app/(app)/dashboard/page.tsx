import { BACKEND_ORIGIN, IdentityUser } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";

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

export default async function DashboardPage() {
  // Layout guard already redirected to /giris if there's no cookie, but the
  // token can still be stale/invalid (e.g. expired) - handle that honestly.
  const token = await getSessionToken();
  const user = token ? await fetchMe(token) : null;

  if (!user) {
    return (
      <div>
        <h1>Hesabim</h1>
        <p className="error-box">
          Oturum bilgisi dogrulanamadi. Lutfen tekrar giris yapmayi deneyin.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1>Hesabim</h1>
      <p>
        <strong>E-posta:</strong> {user.email}
      </p>
      <p>
        <strong>Gorunen ad:</strong> {user.display_name ?? "(belirtilmemis)"}
      </p>
    </div>
  );
}
