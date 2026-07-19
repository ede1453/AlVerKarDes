"use client";

import { useLocale, useTranslations } from "next-intl";
import { routing } from "@/i18n/routing";
import { usePathname, useRouter } from "@/i18n/navigation";

// Switches locale for the *current* path (preserving params/query), e.g. on
// /en/urun/abc123 switching to German goes to /de/urun/abc123, not the
// homepage. Uses next-intl's locale-aware usePathname/useRouter so dynamic
// route params are re-inserted correctly rather than string-splicing the URL.
export default function LocaleSwitcher() {
  const t = useTranslations("common.localeSwitcher");
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();

  return (
    <span className="locale-switcher">
      {routing.locales.map((loc) => (
        <button
          key={loc}
          type="button"
          className="btn locale-switcher-btn"
          disabled={loc === locale}
          aria-current={loc === locale}
          onClick={() => router.replace(pathname, { locale: loc })}
        >
          {t(loc)}
        </button>
      ))}
    </span>
  );
}
