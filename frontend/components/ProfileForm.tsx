"use client";

import { useState, FormEvent } from "react";
import { useTranslations } from "next-intl";
import { IdentityUser } from "@/lib/backend";

interface ProfileFormProps {
  userId: string;
  initialUser: IdentityUser;
}

type Status = "idle" | "saving" | "saved" | "error";
type ErrorKind = "validation" | "generic";

// Must match the backend's SUPPORTED_LOCALES exactly
// (app/domains/identity/schemas.py) - not a free-text field, these two
// values are the only ones the PATCH /identity/me endpoint accepts.
const LANGUAGES = ["de", "en"] as const;

export default function ProfileForm({ userId, initialUser }: ProfileFormProps) {
  const t = useTranslations("profile");
  const [displayName, setDisplayName] = useState(initialUser.display_name ?? "");
  const [language, setLanguage] = useState(initialUser.preferred_language ?? "en");
  const [country, setCountry] = useState(initialUser.preferred_country ?? "DE");
  const [currency, setCurrency] = useState(initialUser.preferred_currency ?? "");
  const [status, setStatus] = useState<Status>("idle");
  const [errorKind, setErrorKind] = useState<ErrorKind>("generic");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setStatus("saving");
    try {
      // Full replace, not a partial patch - the backend requires all three
      // fields on every PATCH (display_name may be empty/omitted, but
      // language/country are always submitted since there's no "leave
      // unchanged" semantics in this request shape).
      const res = await fetch("/api/proxy/identity/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          display_name: displayName.trim().length > 0 ? displayName.trim() : null,
          preferred_language: language,
          preferred_country: country.trim().toUpperCase(),
        }),
      });
      if (!res.ok) {
        setErrorKind(res.status === 422 ? "validation" : "generic");
        setStatus("error");
        return;
      }
      const body = (await res.json()) as IdentityUser;
      // Displayed state comes from the real PATCH response, not an echo of
      // what the user typed - proves the save actually persisted the
      // values we think it did (e.g. country really got uppercased
      // server-side).
      setDisplayName(body.display_name ?? "");
      setLanguage(body.preferred_language ?? language);
      setCountry(body.preferred_country ?? country);
      setCurrency(body.preferred_currency ?? currency);
      setStatus("saved");
    } catch {
      setErrorKind("generic");
      setStatus("error");
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-field">
        <label htmlFor="display_name">{t("displayNameLabel")}</label>
        <input
          id="display_name"
          type="text"
          maxLength={160}
          value={displayName}
          onChange={(e) => {
            setStatus("idle");
            setDisplayName(e.target.value);
          }}
        />
      </div>

      <div className="form-field">
        <label htmlFor="preferred_language">{t("languageLabel")}</label>
        <select
          id="preferred_language"
          value={language}
          onChange={(e) => {
            setStatus("idle");
            setLanguage(e.target.value);
          }}
        >
          {LANGUAGES.map((code) => (
            <option key={code} value={code}>
              {t(`languageOption.${code}`)}
            </option>
          ))}
        </select>
        <p className="field-note">{t("languageNote")}</p>
      </div>

      <div className="form-field">
        <label htmlFor="preferred_country">{t("countryLabel")}</label>
        <input
          id="preferred_country"
          type="text"
          maxLength={2}
          value={country}
          onChange={(e) => {
            setStatus("idle");
            setCountry(e.target.value.toUpperCase());
          }}
          onBlur={(e) => setCountry(e.target.value.trim().toUpperCase())}
        />
      </div>

      {currency && (
        <div className="form-field">
          <label>{t("currencyLabel")}</label>
          <p>{currency}</p>
        </div>
      )}

      <button type="submit" className="btn" disabled={status === "saving"}>
        {status === "saving" ? t("saving") : t("saveButton")}
      </button>
      {status === "saved" && <p className="notice-box">{t("savedMessage")}</p>}
      {status === "error" && (
        <p className="error-box">
          {errorKind === "validation" ? t("validationError") : t("saveError")}
        </p>
      )}
    </form>
  );
}
