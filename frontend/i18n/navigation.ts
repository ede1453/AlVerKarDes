import { createNavigation } from "next-intl/navigation";
import { routing } from "./routing";

// Locale-aware Link/useRouter/usePathname/redirect, scoped to our routing
// config (locales, defaultLocale, localePrefix). Use these instead of the
// plain next/link / next/navigation exports anywhere under app/[locale]/...
export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);
