"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

interface RemoveFromWatchlistButtonProps {
  itemId: string;
}

export default function RemoveFromWatchlistButton({ itemId }: RemoveFromWatchlistButtonProps) {
  const t = useTranslations("watchlist");
  const router = useRouter();
  const [removing, setRemoving] = useState(false);
  const [error, setError] = useState(false);

  async function handleClick() {
    setRemoving(true);
    setError(false);
    try {
      const res = await fetch(`/api/proxy/watchlist/items/${itemId}/deactivate`, {
        method: "POST",
      });
      if (!res.ok) {
        setError(true);
        setRemoving(false);
        return;
      }
      router.refresh();
    } catch {
      setError(true);
      setRemoving(false);
    }
  }

  return (
    <div>
      <button type="button" className="btn" onClick={handleClick} disabled={removing}>
        {removing ? t("removing") : t("removeButton")}
      </button>
      {error && <p className="error-box">{t("removeError")}</p>}
    </div>
  );
}
