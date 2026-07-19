import type { Locale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import ResetPasswordForm from "@/components/ResetPasswordForm";

interface ResetPasswordPageProps {
  // params: locale, already validated against routing.locales by the
  // [locale]/layout.tsx guard above. searchParams carries the ?token= from
  // the reset-link email (see auth_core_router.issue_password_reset).
  params: Promise<{ locale: Locale }>;
  searchParams: Promise<{ token?: string | string[] }>;
}

export default async function ResetPasswordPage({ params, searchParams }: ResetPasswordPageProps) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("resetPassword");
  const { token: rawToken } = await searchParams;
  const token = typeof rawToken === "string" ? rawToken : undefined;

  return (
    <div>
      <h1>{t("heading")}</h1>
      {token ? (
        <ResetPasswordForm token={token} />
      ) : (
        // Honest "missing/invalid link" state - do not silently render a
        // broken form with no token to submit.
        <p className="error-box">{t("missingTokenMessage")}</p>
      )}
    </div>
  );
}
