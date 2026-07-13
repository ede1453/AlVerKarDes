from app.domains.decision.consumer_decision_engine import ConsumerDecisionInput


class DecisionInputBuilder:
    def from_grouped_recommendation(self, *, selected_group: dict, recommendation: dict, user_context: dict | None = None) -> ConsumerDecisionInput:
        user_context = user_context or {}

        best_offer = selected_group.get("best_offer") or {}
        confidence = selected_group.get("confidence") or {}
        trace = recommendation.get("agent_trace") or {}

        price_trace = trace.get("price_intelligence") or {}
        fraud_trace = trace.get("fraud_agent") or {}
        review_trace = trace.get("review_analyst") or {}

        price_evidence = self._find_evidence(recommendation, "PRICE_HISTORY")
        fraud_evidence = self._find_evidence(recommendation, "FRAUD_ANALYSIS")
        price_data = price_evidence.get("data") or {}
        fraud_data = fraud_evidence.get("data") or {}

        return ConsumerDecisionInput(
            price_signal=price_trace.get("price_signal") or self._map_recommendation_decision(recommendation.get("decision")),
            price_confidence=float(price_trace.get("confidence") or price_evidence.get("confidence") or recommendation.get("confidence") or 0),
            fake_discount_risk=price_trace.get("fake_discount_risk") or price_data.get("fake_discount_risk") or "LOW",
            review_reliability=review_trace.get("review_reliability") or "UNKNOWN",
            fraud_risk=fraud_trace.get("risk_level") or fraud_data.get("risk_level") or "UNKNOWN",
            match_confidence=float(confidence.get("best_match_group_score") or best_offer.get("match_group_score") or 0),
            availability=best_offer.get("availability"),
            current_price=self._float_or_none(price_data.get("current_price") or best_offer.get("price")),
            historical_lowest=self._float_or_none(price_data.get("historical_lowest")),
            historical_average=self._float_or_none(price_data.get("historical_average")),
            store_trust_score=float(user_context.get("store_trust_score") or 80),
            extra={
                "selected_group_id": selected_group.get("match_group_id"),
                "best_offer_source": best_offer.get("source"),
                "recommendation_id": recommendation.get("recommendation_id"),
            },
        )

    def _find_evidence(self, recommendation: dict, evidence_type: str) -> dict:
        for item in recommendation.get("evidence") or []:
            if item.get("type") == evidence_type:
                return item
        return {}

    def _map_recommendation_decision(self, decision: str | None) -> str:
        if decision == "BUY":
            return "BUY"
        if decision in {"WAIT", "CONSIDER_ALTERNATIVE", "DO_NOT_BUY"}:
            return "WAIT"
        return "INSUFFICIENT_HISTORY"

    def _float_or_none(self, value):
        if value is None:
            return None
        return float(value)
