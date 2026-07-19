"use client";

import { useState, FormEvent } from "react";
import { useTranslations } from "next-intl";
import { Link, useRouter } from "@/i18n/navigation";

export default function RegisterPage() {
  const t = useTranslations("register");
  const tAuth = useTranslations("auth");
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          password,
          display_name: displayName || undefined,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(
          typeof body?.detail === "string" ? body.detail : t("errorFallback", { status: res.status })
        );
        setSubmitting(false);
        return;
      }
      setSuccess(true);
      setSubmitting(false);
      setTimeout(() => router.push("/giris"), 1200);
    } catch {
      setError(tAuth("networkError"));
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <div>
        <h1>{t("successHeading")}</h1>
        <p className="notice-box">
          {t("successMessage")} <Link href="/giris">{t("goNow")}</Link>
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1>{t("heading")}</h1>
      {error && <p className="error-box">{error}</p>}
      <form onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="email">{tAuth("emailLabel")}</label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="form-field">
          <label htmlFor="password">{t("passwordLabel")}</label>
          <input
            id="password"
            type="password"
            required
            minLength={8}
            maxLength={128}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <div className="form-field">
          <label htmlFor="displayName">{t("displayNameLabel")}</label>
          <input
            id="displayName"
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
        </div>
        <button type="submit" className="btn" disabled={submitting}>
          {submitting ? t("submitting") : t("submitButton")}
        </button>
      </form>
    </div>
  );
}
