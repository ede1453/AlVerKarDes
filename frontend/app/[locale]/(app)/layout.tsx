import { hasLocale } from "next-intl";
import { notFound } from "next/navigation";
import { routing } from "@/i18n/routing";
import { redirect } from "@/i18n/navigation";
import { getSessionToken } from "@/lib/session";

// Auth guard for everything under the (app) route group: dashboard,
// watchlist, etc. No session cookie -> redirect to /giris (in the current
// locale).
export default async function AppLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale: rawLocale } = await params;
  if (!hasLocale(routing.locales, rawLocale)) {
    notFound();
  }
  const locale = rawLocale;
  const token = await getSessionToken();
  if (!token) {
    redirect({ href: "/giris", locale });
  }

  return <>{children}</>;
}
