from app.domains.trust_intelligence.trust_models import (
    TrustEvaluationInput,
    TrustEvaluationResult,
    TrustProfile,
    TrustSignal,
)


class TrustIntelligenceEngine:
    def build_profile(self, *, entity_type: str, entity_id: str, signal: TrustSignal) -> TrustProfile:
        total = max(signal.total_count, signal.positive_count + signal.negative_count + signal.neutral_count)

        if total == 0:
            trust_score = 70
        else:
            positive_score = (signal.positive_count / total) * 100
            negative_penalty = (signal.negative_count / total) * 35
            fraud_penalty = min(50, signal.fraud_count * 20)
            return_penalty = min(20, signal.return_count * 5)
            trust_score = round(positive_score - negative_penalty - fraud_penalty - return_penalty)
            trust_score = self._clamp(trust_score, 0, 100)

        reliability_score = self._reliability_score(total=total, fraud_count=signal.fraud_count)

        return TrustProfile(
            entity_type=entity_type,
            entity_id=entity_id,
            trust_score=trust_score,
            reliability_score=reliability_score,
            positive_count=signal.positive_count,
            negative_count=signal.negative_count,
            fraud_count=signal.fraud_count,
        )

    def evaluate(
        self,
        *,
        data: TrustEvaluationInput,
        user_profile: TrustProfile | None = None,
        store_profile: TrustProfile | None = None,
        product_profile: TrustProfile | None = None,
        community_profile: TrustProfile | None = None,
    ) -> TrustEvaluationResult:
        user_score = self._score(user_profile)
        store_score = self._score(store_profile)
        product_score = self._score(product_profile)
        community_score = self._score(community_profile)

        reason_codes: list[str] = []
        adjustment = 0

        if user_score >= 85:
            adjustment += 4
            reason_codes.append("HIGH_USER_TRUST")
        elif user_score < 45:
            adjustment -= 8
            reason_codes.append("LOW_USER_TRUST")

        if store_score >= 85:
            adjustment += 4
            reason_codes.append("HIGH_STORE_TRUST")
        elif store_score < 45:
            adjustment -= 10
            reason_codes.append("LOW_STORE_TRUST")

        if product_score >= 85:
            adjustment += 3
            reason_codes.append("HIGH_PRODUCT_TRUST")
        elif product_score < 45:
            adjustment -= 7
            reason_codes.append("LOW_PRODUCT_TRUST")

        if community_score >= 85:
            adjustment += 5
            reason_codes.append("POSITIVE_COMMUNITY_SIGNAL")
        elif community_score < 45:
            adjustment -= 8
            reason_codes.append("NEGATIVE_COMMUNITY_SIGNAL")

        feedback_adjustment = int(data.feedback_summary.get("confidence_adjustment", 0) or 0)
        if feedback_adjustment:
            adjustment += self._clamp(feedback_adjustment, -10, 10)
            reason_codes.append("FEEDBACK_LEARNING_ADJUSTMENT")

        risk_modifier = self._risk_modifier(
            store_score=store_score,
            product_score=product_score,
            community_score=community_score,
        )

        if risk_modifier == "HIGH_RISK":
            adjustment -= 5
            reason_codes.append("TRUST_RISK_MODIFIER_APPLIED")

        final_confidence = self._clamp(data.base_confidence + adjustment, 0, 100)

        if not reason_codes:
            reason_codes.append("NEUTRAL_TRUST_SIGNAL")

        return TrustEvaluationResult(
            decision_id=data.decision_id,
            user_trust_score=user_score,
            community_score=community_score,
            store_score=store_score,
            product_score=product_score,
            recommendation_confidence_adjustment=adjustment,
            final_confidence=final_confidence,
            risk_modifier=risk_modifier,
            reason_codes=reason_codes,
        )

    def _score(self, profile: TrustProfile | None) -> int:
        if profile is None:
            return 70
        return self._clamp(profile.trust_score, 0, 100)

    def _reliability_score(self, *, total: int, fraud_count: int) -> int:
        if total <= 0:
            return 50
        score = min(100, 45 + total * 5) - min(40, fraud_count * 15)
        return self._clamp(score, 0, 100)

    def _risk_modifier(self, *, store_score: int, product_score: int, community_score: int) -> str:
        if store_score < 40 or product_score < 40 or community_score < 40:
            return "HIGH_RISK"
        if store_score >= 80 and product_score >= 80 and community_score >= 80:
            return "LOW_RISK"
        return "MEDIUM_RISK"

    def _clamp(self, value: int, lower: int, upper: int) -> int:
        return max(lower, min(upper, value))
