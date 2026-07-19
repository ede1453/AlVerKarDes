"use client";

import { useState, FormEvent } from "react";
import { useTranslations } from "next-intl";
import { Link, useRouter } from "@/i18n/navigation";

export default function LoginPage() {
  const t = useTranslations("login");
  const tAuth = useTranslations("auth");
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(
          typeof body?.detail === "string" ? body.detail : t("errorFallback", { status: res.status })
        );
        setSubmitting(false);
        return;
      }
      router.push("/dashboard");
      router.refresh();
    } catch {
      setError(tAuth("networkError"));
      setSubmitting(false);
    }
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
          <label htmlFor="password">{tAuth("passwordLabel")}</label>
          <input
            id="password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button type="submit" className="btn" disabled={submitting}>
          {submitting ? t("submitting") : t("submitButton")}
        </button>
      </form>
      <p style={{ marginTop: "1rem" }}>
        <Link href="/sifremi-unuttum">{t("forgotPasswordLink")}</Link>
      </p>
    </div>
  );
}
