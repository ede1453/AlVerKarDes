import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { cookies } from "next/headers";
import { hasLocale, NextIntlClientProvider } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { routing } from "@/i18n/routing";
import { Link } from "@/i18n/navigation";
import { SESSION_COOKIE_NAME } from "@/lib/backend";
import LocaleSwitcher from "@/components/LocaleSwitcher";

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: rawLocale } = await params;
  const locale = hasLocale(routing.locales, rawLocale) ? rawLocale : routing.defaultLocale;
  const t = await getTranslations({ locale, namespace: "common.meta" });
  return {
    title: t("title"),
    description: t("description"),
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  // Enables static rendering for pages under this segment.
  setRequestLocale(locale);

  const t = await getTranslations({ locale, namespace: "common.nav" });
  const cookieStore = await cookies();
  const isLoggedIn = Boolean(cookieStore.get(SESSION_COOKIE_NAME)?.value);

  return (
    <NextIntlClientProvider locale={locale}>
      <header className="site-header">
        <Link href="/">
          <strong>AlVerKarDes</strong>
        </Link>
        <nav>
          <Link href="/firsatlar">{t("deals")}</Link>
          {isLoggedIn ? (
            <>
              <Link href="/dashboard">{t("account")}</Link>
              <Link href="/watchlist">{t("watchlist")}</Link>
              <form action="/api/auth/logout" method="post">
                <button type="submit" className="btn">
                  {t("logout")}
                </button>
              </form>
            </>
          ) : (
            <>
              <Link href="/giris">{t("login")}</Link>
              <Link href="/kayit">{t("register")}</Link>
            </>
          )}
          <LocaleSwitcher />
        </nav>
      </header>
      <main className="site-main">{children}</main>
    </NextIntlClientProvider>
  );
}
