"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

interface AddToWatchlistButtonProps {
  userId: string;
  productKey: string;
  query: string;
}

type Status = "idle" | "submitting" | "added" | "error";

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
      <button type="button" className="btn" onClick={handleClick} disabled={status === "submitting" || status === "added"}>
        {status === "submitting"
          ? t("watchlistAdding")
          : status === "added"
            ? t("watchlistAdded")
            : t("watchlistAddButton")}
      </button>
      {status === "error" && <p className="error-box">{t("watchlistAddError")}</p>}
    </div>
  );
}
