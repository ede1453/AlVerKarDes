class AIExplanationEngine:
    def explain(
        self,
        *,
        language: str = "en",
        tone: str = "clear",
        agent_decision: dict | None = None,
        deal_detection: dict | None = None,
        discount_intelligence: dict | None = None,
        smart_alert: dict | None = None,
        price_prediction: dict | None = None,
    ) -> dict:
        decision = (agent_decision or {}).get("decision")
        deal_level = (deal_detection or {}).get("deal_level")
        discount_quality = (discount_intelligence or {}).get("discount_quality")
        fake_risk = (discount_intelligence or {}).get("fake_discount_risk")
        alert_level = (smart_alert or {}).get("alert_level")
        prediction_hint = (price_prediction or {}).get("recommendation_hint")

        bullet_points: list[str] = []
        risk_notes: list[str] = []
        next_actions: list[str] = []

        if decision:
            bullet_points.append(f"Agent decision: {decision}.")
        if deal_level:
            bullet_points.append(f"Deal signal: {deal_level}.")
        if discount_quality:
            bullet_points.append(f"Discount quality: {discount_quality}.")
        if prediction_hint:
            bullet_points.append(f"Price prediction hint: {prediction_hint}.")
        if alert_level:
            bullet_points.append(f"Alert level: {alert_level}.")

        if fake_risk in ["MEDIUM", "HIGH"]:
            risk_notes.append(f"Fake discount risk is {fake_risk.lower()}; verify historical price before buying.")
        elif fake_risk == "LOW":
            risk_notes.append("Fake discount risk is low based on available signals.")

        if decision == "BUY_NOW" or deal_level == "EXCELLENT_DEAL":
            headline = "This looks like a strong buy opportunity"
            next_actions.append("Check final seller terms before purchase.")
            next_actions.append("Confirm warranty, return policy, delivery cost, and final checkout price.")
        elif prediction_hint == "WAIT_OR_WATCH":
            headline = "Waiting may be reasonable"
            next_actions.append("Keep this product on your watchlist.")
            next_actions.append("Wait for a stronger price or deal signal.")
        else:
            headline = "More comparison is recommended"
            next_actions.append("Compare at least one more marketplace.")
            next_actions.append("Check whether the discount is based on a real historical price.")

        if not bullet_points:
            bullet_points.append("There are not enough signals for a confident explanation.")

        explanation_text = self._compose_text(
            headline=headline,
            bullet_points=bullet_points,
            risk_notes=risk_notes,
            tone=tone,
            language=language,
        )

        return {
            "mode": "DETERMINISTIC_EXPLANATION",
            "language": language,
            "tone": tone,
            "headline": headline,
            "explanation_text": explanation_text,
            "bullet_points": bullet_points,
            "risk_notes": risk_notes,
            "next_actions": next_actions,
        }

    def _compose_text(self, *, headline: str, bullet_points: list[str], risk_notes: list[str], tone: str, language: str) -> str:
        parts = [headline + "."]
        parts.extend(bullet_points)
        parts.extend(risk_notes)
        if tone == "concise":
            return " ".join(parts[:4])
        return " ".join(parts)
