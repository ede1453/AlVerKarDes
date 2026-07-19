"use client";

import { useState, FormEvent } from "react";
import { useTranslations } from "next-intl";
import { Link, useRouter } from "@/i18n/navigation";

interface ResetPasswordFormProps {
  token: string;
}

export default function ResetPasswordForm({ token }: ResetPasswordFormProps) {
  const t = useTranslations("resetPassword");
  const tAuth = useTranslations("auth");
  const router = useRouter();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    // No backend endpoint double-checks this, so the match check has to
    // happen client-side before we ever submit.
    if (newPassword !== confirmPassword) {
      setError(t("mismatchError"));
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch("/api/auth/password-reset/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: newPassword }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        // The backend's detail is either a plain error code
        // (TOKEN_INVALID/TOKEN_EXPIRED/...) or a comma-joined password
        // policy violation string - show it as-is rather than mapping every
        // code to a bespoke localized string.
        setError(typeof body?.detail === "string" ? body.detail : t("genericFailure"));
        setSubmitting(false);
        return;
      }
      // Same pattern as the register page's post-success redirect: show a
      // local success notice, then redirect to /giris after a short delay.
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
      <p className="notice-box">
        {t("successMessage")} <Link href="/giris">{t("goNow")}</Link>
      </p>
    );
  }

  return (
    <>
      {error && <p className="error-box">{error}</p>}
      <form onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="newPassword">{t("newPasswordLabel")}</label>
          <input
            id="newPassword"
            type="password"
            required
            minLength={12}
            maxLength={128}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
        </div>
        <div className="form-field">
          <label htmlFor="confirmPassword">{t("confirmPasswordLabel")}</label>
          <input
            id="confirmPassword"
            type="password"
            required
            minLength={12}
            maxLength={128}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
        </div>
        <button type="submit" className="btn" disabled={submitting}>
          {submitting ? t("submitting") : t("submitButton")}
        </button>
      </form>
    </>
  );
}
