"use client";

import { useState, FormEvent } from "react";
import { useTranslations } from "next-intl";

// Enumeration-safety requirement (see ADR/task): the UI must show the exact
// same success message whether or not the submitted email belongs to a real
// account - the backend already guarantees an identical 200 response either
// way, this page must not add a client-side signal that leaks the
// difference. Only 429 (rate limit) is a real, safe-to-show-distinctly signal.
type Status = "idle" | "success" | "rateLimited" | "networkError";

export default function ForgotPasswordPage() {
  const t = useTranslations("forgotPassword");
  const tAuth = useTranslations("auth");
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await fetch("/api/auth/password-reset/issue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier: email }),
      });
      if (res.status === 429) {
        setStatus("rateLimited");
        setSubmitting(false);
        return;
      }
      if (res.ok) {
        setStatus("success");
        setSubmitting(false);
        return;
      }
      // Any other non-ok status here is a real infra failure (proxy could
      // not reach the backend, malformed request, etc), not an
      // enumeration signal - honest error, not a fabricated success.
      setStatus("networkError");
      setSubmitting(false);
    } catch {
      setStatus("networkError");
      setSubmitting(false);
    }
  }

  if (status === "success") {
    return (
      <div>
        <h1>{t("heading")}</h1>
        <p className="notice-box">{t("successMessage")}</p>
      </div>
    );
  }

  return (
    <div>
      <h1>{t("heading")}</h1>
      {status === "rateLimited" && <p className="error-box">{t("rateLimitedMessage")}</p>}
      {status === "networkError" && <p className="error-box">{tAuth("networkError")}</p>}
      <p>{t("intro")}</p>
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
        <button type="submit" className="btn" disabled={submitting}>
          {submitting ? t("submitting") : t("submitButton")}
        </button>
      </form>
    </div>
  );
}
