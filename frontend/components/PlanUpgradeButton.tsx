"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";
import { Subscription } from "@/lib/backend";

interface PlanUpgradeButtonProps {
  userId: string;
  initialSubscription: Subscription;
}

type Status = "idle" | "submitting" | "error";

export default function PlanUpgradeButton({ userId, initialSubscription }: PlanUpgradeButtonProps) {
  const t = useTranslations("billing");
  const router = useRouter();
  const [subscription, setSubscription] = useState<Subscription>(initialSubscription);
  const [status, setStatus] = useState<Status>("idle");

  async function handleUpgrade() {
    setStatus("submitting");
    try {
      const res = await fetch("/api/proxy/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, plan: "PREMIUM" }),
      });
      if (!res.ok) {
        setStatus("error");
        return;
      }
      // Displayed state comes from the real POST response, not an echo of
      // what we asked for - proves the mock checkout actually persisted.
      const body = (await res.json()) as Subscription;
      setSubscription(body);
      setStatus("idle");
      // Re-run the (app) layout's Server Components so pages like
      // /bildirimler that gate on the tier reflect the new state without a
      // full manual reload.
      router.refresh();
    } catch {
      setStatus("error");
    }
  }

  async function handleCancel() {
    setStatus("submitting");
    try {
      const res = await fetch("/api/proxy/billing/cancel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      });
      if (!res.ok) {
        setStatus("error");
        return;
      }
      const body = (await res.json()) as Subscription;
      setSubscription(body);
      setStatus("idle");
      router.refresh();
    } catch {
      setStatus("error");
    }
  }

  return (
    <div style={{ marginTop: "1.5rem" }}>
      {subscription.tier === "PREMIUM" ? (
        <button
          type="button"
          className="btn"
          onClick={handleCancel}
          disabled={status === "submitting"}
        >
          {status === "submitting" ? t("cancelling") : t("cancelButton")}
        </button>
      ) : (
        <button
          type="button"
          className="btn"
          onClick={handleUpgrade}
          disabled={status === "submitting"}
        >
          {status === "submitting" ? t("upgrading") : t("upgradeButton")}
        </button>
      )}
      {status === "error" && <p className="error-box">{t("actionError")}</p>}
      {subscription.provider_reference && (
        <p className="field-note">{t("providerReferenceLabel", { reference: subscription.provider_reference })}</p>
      )}
    </div>
  );
}
