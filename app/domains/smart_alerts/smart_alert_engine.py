class SmartAlertEngine:
    def decide(
        self,
        *,
        user_id: str | None,
        product_key: str,
        deal_detection: dict | None = None,
        price_prediction: dict | None = None,
        personalization: dict | None = None,
        channels: list[str] | None = None,
    ) -> dict:
        score = 0
        reasons: list[str] = []
        channels = channels or ["in_app"]

        deal_level = (deal_detection or {}).get("deal_level")
        deal_score = int((deal_detection or {}).get("deal_score") or 0)

        if deal_level == "EXCELLENT_DEAL":
            score += 45
            reasons.append("EXCELLENT_DEAL")
        elif deal_level == "GOOD_DEAL":
            score += 30
            reasons.append("GOOD_DEAL")
        elif deal_level == "FAIR_DEAL":
            score += 15
            reasons.append("FAIR_DEAL")

        if deal_score >= 85:
            score += 15
            reasons.append("HIGH_DEAL_SCORE")

        hint = (price_prediction or {}).get("recommendation_hint")
        if hint == "BUY_SOON":
            score += 25
            reasons.append("PRICE_PREDICTION_BUY_SOON")
        elif hint == "WAIT_OR_WATCH":
            score -= 10
            reasons.append("PRICE_PREDICTION_WAIT")
        elif hint == "INSUFFICIENT_HISTORY":
            score -= 5
            reasons.append("INSUFFICIENT_PRICE_HISTORY")

        if personalization and personalization.get("top_offer"):
            p_score = int(personalization["top_offer"].get("personalization_score") or 0)
            if p_score >= 85:
                score += 15
                reasons.append("HIGH_PERSONALIZATION_MATCH")
            elif p_score < 40:
                score -= 15
                reasons.append("LOW_PERSONALIZATION_MATCH")

        score = max(0, min(100, score))
        should_alert = score >= 70

        if score >= 90:
            alert_level = "URGENT"
        elif score >= 70:
            alert_level = "HIGH"
        elif score >= 50:
            alert_level = "WATCH"
        else:
            alert_level = "NONE"

        if should_alert:
            title = "Strong deal detected"
            message = "This product currently has strong buy signals."
        elif alert_level == "WATCH":
            title = "Worth watching"
            message = "This product has some useful signals, but not enough for an alert."
        else:
            title = "No alert"
            message = "No strong alert signal was detected."

        if not reasons:
            reasons.append("NO_STRONG_ALERT_SIGNALS")

        return {
            "should_alert": should_alert,
            "alert_level": alert_level,
            "alert_score": score,
            "title": title,
            "message": message,
            "channels": channels,
            "reasons": reasons,
        }
