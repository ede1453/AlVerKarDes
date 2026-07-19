"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
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
        setError(typeof body?.detail === "string" ? body.detail : `Kayit basarisiz (${res.status})`);
        setSubmitting(false);
        return;
      }
      setSuccess(true);
      setSubmitting(false);
      setTimeout(() => router.push("/giris"), 1200);
    } catch {
      setError("Sunucuya ulasilamadi.");
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <div>
        <h1>Kayit basarili</h1>
        <p className="notice-box">
          Hesabin olusturuldu. Giris sayfasina yonlendiriliyorsun...{" "}
          <Link href="/giris">Hemen git</Link>
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1>Kayit ol</h1>
      {error && <p className="error-box">{error}</p>}
      <form onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="email">E-posta</label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="form-field">
          <label htmlFor="password">Sifre (8-128 karakter)</label>
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
          <label htmlFor="displayName">Gorunen ad (opsiyonel)</label>
          <input
            id="displayName"
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
        </div>
        <button type="submit" className="btn" disabled={submitting}>
          {submitting ? "Kayit olunuyor..." : "Kayit ol"}
        </button>
      </form>
    </div>
  );
}
