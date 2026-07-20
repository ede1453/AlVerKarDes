"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";

interface AddToWatchlistButtonProps {
  userId: string;
  productKey: string;
  query: string;
}

type Status = "idle" | "submitting" | "added" | "error" | "limit_reached";

export default function AddToWatchlistButton({ userId, productKey, query }: AddToWatchlistButtonProps) {
  const t = useTranslations("productDetail");
  const [status, setStatus] = useState<Status>("idle");

  async function handleClick() {
    setStatus("submitting");
    try {
      const res = await fetch("/api/proxy/watchlist/items", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, product_key: productKey, query }),
      });
      if (!res.ok) {
        // BILL-001: FREE tier watchlist cap returns a specific error code
        // in the body (see app/api/v1/watchlist_router.py) - surface a
        // targeted upsell message instead of the generic error for that
        // case specifically.
        if (res.status === 403) {
          const body = await res.json().catch(() => null);
          if (body?.detail?.code === "WATCHLIST_LIMIT_REACHED") {
            setStatus("limit_reached");
            return;
          }
        }
        setStatus("error");
        return;
      }
      setStatus("added");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div style={{ marginTop: "1rem" }}>
      <button
        type="button"
        className="btn"
        onClick={handleClick}
        disabled={status === "submitting" || status === "added" || status === "limit_reached"}
      >
        {status === "submitting"
          ? t("watchlistAdding")
          : status === "added"
            ? t("watchlistAdded")
            : t("watchlistAddButton")}
      </button>
      {status === "error" && <p className="error-box">{t("watchlistAddError")}</p>}
      {status === "limit_reached" && (
        <p className="error-box">
          {t("watchlistLimitReached")} <Link href="/abonelik">{t("watchlistLimitReachedLink")}</Link>
        </p>
      )}
    </div>
  );
}
