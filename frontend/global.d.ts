import en from "./messages/en.json";
import { routing } from "./i18n/routing";

// next-intl typed messages: referencing a message key that doesn't exist in
// messages/en.json becomes a tsc compile error, not just a runtime warning.
// See i18n/routing.ts for the locale list and messages/en.json as the
// canonical message shape (both locales must match it exactly - enforced at
// runtime/CI by scripts/check-i18n-parity.mjs).
declare module "next-intl" {
  interface AppConfig {
    Locale: (typeof routing.locales)[number];
    Messages: typeof en;
  }
}
