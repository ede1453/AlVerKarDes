import type { Metadata } from "next";
import { cookies } from "next/headers";
import Link from "next/link";
import "./globals.css";
import { SESSION_COOKIE_NAME } from "@/lib/backend";

export const metadata: Metadata = {
  title: "AlVerKarDes",
  description: "AlVerKarDes - urun arama ve fiyat takibi",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const cookieStore = await cookies();
  const isLoggedIn = Boolean(cookieStore.get(SESSION_COOKIE_NAME)?.value);

  return (
    <html lang="tr">
      <body>
        <header className="site-header">
          <Link href="/">
            <strong>AlVerKarDes</strong>
          </Link>
          <nav>
            {isLoggedIn ? (
              <>
                <Link href="/dashboard">Hesabim</Link>
                <Link href="/watchlist">Takip Listem</Link>
                <form action="/api/auth/logout" method="post">
                  <button type="submit" className="btn">
                    Cikis yap
                  </button>
                </form>
              </>
            ) : (
              <>
                <Link href="/giris">Giris yap</Link>
                <Link href="/kayit">Kayit ol</Link>
              </>
            )}
          </nav>
        </header>
        <main className="site-main">{children}</main>
      </body>
    </html>
  );
}
