import { getLocale } from "next-intl/server";
import "./globals.css";

// True root layout, required by Next.js App Router (must define <html>/<body>
// exactly once for the whole app). Deliberately minimal - the nav, metadata,
// and NextIntlClientProvider live in app/[locale]/layout.tsx so this file
// doesn't need to know about locale-specific content, only the <html lang>
// attribute (via next-intl's getLocale(), resolved from the request the
// middleware already routed to a locale).
export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await getLocale();

  return (
    <html lang={locale}>
      <body>{children}</body>
    </html>
  );
}
