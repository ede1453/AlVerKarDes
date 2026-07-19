"use client";

import { useState, FormEvent } from "react";
import { useTranslations } from "next-intl";
import {
  NotificationPreferences,
  NotificationPreferencesUpdateResponse,
} from "@/lib/backend";

interface NotificationPreferencesFormProps {
  userId: string;
  initialPreferences: NotificationPreferences;
}

type Status = "idle" | "saving" | "saved" | "error";

// Must match the backend's NotificationChannelRouter.SUPPORTED_CHANNELS
// exactly (app/domains/deal_notifications/service.py) - not a free-text
// field, these three values are the only ones the backend accepts/routes.
const CHANNELS = ["in_app", "email", "push"] as const;

export default function NotificationPreferencesForm({
  userId,
  initialPreferences,
}: NotificationPreferencesFormProps) {
  const t = useTranslations("notificationPreferences");
  const [preferences, setPreferences] = useState<NotificationPreferences>(initialPreferences);
  const [status, setStatus] = useState<Status>("idle");

  function toggleChannel(channel: string) {
    setStatus("idle");
    setPreferences((prev) => {
      const enabled = prev.enabled_channels.includes(channel);
      return {
        ...prev,
        enabled_channels: enabled
          ? prev.enabled_channels.filter((c) => c !== channel)
          : [...prev.enabled_channels, channel],
      };
    });
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setStatus("saving");
    try {
      // Full replace, not a partial patch - the backend applies its own
      // defaults for any omitted field, so we always submit the complete
      // current state (every field), not just whatever the user last
      // touched.
      const res = await fetch("/api/proxy/deal-notifications/preferences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          enabled_channels: preferences.enabled_channels,
          minimum_confidence: preferences.minimum_confidence,
          minimum_discount_pct: preferences.minimum_discount_pct,
          quiet_hours_enabled: preferences.quiet_hours_enabled,
          quiet_hours_start: preferences.quiet_hours_start,
          quiet_hours_end: preferences.quiet_hours_end,
        }),
      });
      if (!res.ok) {
        setStatus("error");
        return;
      }
      const body = (await res.json()) as NotificationPreferencesUpdateResponse;
      // Displayed state comes from the real POST response, not an echo of
      // what the user typed - proves the save actually persisted the
      // values we think it did.
      if (body && body.preferences) {
        setPreferences(body.preferences);
      }
      setStatus("saved");
    } catch {
      setStatus("error");
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <fieldset className="form-field">
        <legend>{t("channelsHeading")}</legend>
        {CHANNELS.map((channel) => (
          <label key={channel} style={{ display: "block" }}>
            <input
              type="checkbox"
              checked={preferences.enabled_channels.includes(channel)}
              onChange={() => toggleChannel(channel)}
            />{" "}
            {t(`channel.${channel}`)}
          </label>
        ))}
      </fieldset>

      <div className="form-field">
        <label htmlFor="minimum_confidence">{t("minConfidenceLabel")}</label>
        <input
          id="minimum_confidence"
          type="number"
          min={0}
          max={100}
          value={preferences.minimum_confidence}
          onChange={(e) =>
            setPreferences((prev) => ({
              ...prev,
              minimum_confidence: Number(e.target.value),
            }))
          }
        />
      </div>

      <div className="form-field">
        <label htmlFor="minimum_discount_pct">{t("minDiscountLabel")}</label>
        <input
          id="minimum_discount_pct"
          type="number"
          min={0}
          max={100}
          value={preferences.minimum_discount_pct}
          onChange={(e) =>
            setPreferences((prev) => ({
              ...prev,
              minimum_discount_pct: Number(e.target.value),
            }))
          }
        />
      </div>

      <div className="form-field">
        <label>
          <input
            type="checkbox"
            checked={preferences.quiet_hours_enabled}
            onChange={(e) =>
              setPreferences((prev) => ({
                ...prev,
                quiet_hours_enabled: e.target.checked,
              }))
            }
          />{" "}
          {t("quietHoursEnabledLabel")}
        </label>
      </div>

      <div className="form-field">
        <label htmlFor="quiet_hours_start">{t("quietHoursStartLabel")}</label>
        <input
          id="quiet_hours_start"
          type="time"
          value={preferences.quiet_hours_start}
          onChange={(e) =>
            setPreferences((prev) => ({ ...prev, quiet_hours_start: e.target.value }))
          }
        />
      </div>

      <div className="form-field">
        <label htmlFor="quiet_hours_end">{t("quietHoursEndLabel")}</label>
        <input
          id="quiet_hours_end"
          type="time"
          value={preferences.quiet_hours_end}
          onChange={(e) =>
            setPreferences((prev) => ({ ...prev, quiet_hours_end: e.target.value }))
          }
        />
      </div>

      <button type="submit" className="btn" disabled={status === "saving"}>
        {status === "saving" ? t("saving") : t("saveButton")}
      </button>
      {status === "saved" && <p className="notice-box">{t("savedMessage")}</p>}
      {status === "error" && <p className="error-box">{t("saveError")}</p>}
    </form>
  );
}
