from decimal import Decimal

from app.domains.personalization.personalization_models import (
    PersonalizationResult,
    PersonalizedOfferScore,
    UserPreferenceProfile,
)


class PersonalizationEngine:
    def score(self, *, profile: UserPreferenceProfile, offers: list[dict]) -> PersonalizationResult:
        scored = [self._score_offer(profile, offer) for offer in offers]
        scored = sorted(scored, key=lambda item: (-item.personalization_score, Decimal(str(item.base_price)), item.marketplace))
        top_offer = None if not scored else self._offer_score_to_dict(scored[0])

        return PersonalizationResult(
            user_id=profile.user_id,
            scored_count=len(scored),
            top_offer=top_offer,
            offers=scored,
            metadata={"personalization_version": "personalization_v1"},
        )

    def _score_offer(self, profile: UserPreferenceProfile, offer: dict) -> PersonalizedOfferScore:
        score = 50
        reasons: list[str] = []

        marketplace = offer.get("marketplace", "")
        product_name = offer.get("product_name", "")
        price = Decimal(str(offer.get("price", "0")))

        if marketplace in profile.preferred_marketplaces:
            score += 20
            reasons.append("PREFERRED_MARKETPLACE")

        if marketplace in profile.blocked_marketplaces:
            score -= 60
            reasons.append("BLOCKED_MARKETPLACE")

        normalized_name = product_name.lower()
        for brand in profile.preferred_brands:
            if brand.lower() in normalized_name:
                score += 15
                reasons.append("PREFERRED_BRAND")
                break

        if profile.max_price is not None and price <= Decimal(str(profile.max_price)):
            score += 10
            reasons.append("WITHIN_BUDGET")
        elif profile.max_price is not None and price > Decimal(str(profile.max_price)):
            score -= 15
            reasons.append("ABOVE_BUDGET")

        score = max(0, min(100, score))

        if not reasons:
            reasons.append("NEUTRAL_MATCH")

        return PersonalizedOfferScore(
            offer_id=offer.get("id") or offer.get("offer_id") or "",
            marketplace=marketplace,
            product_name=product_name,
            base_price=str(offer.get("price")),
            personalization_score=score,
            reasons=reasons,
            metadata={"risk_tolerance": profile.risk_tolerance},
        )

    def _offer_score_to_dict(self, item: PersonalizedOfferScore):
        return {
            "offer_id": item.offer_id,
            "marketplace": item.marketplace,
            "product_name": item.product_name,
            "base_price": item.base_price,
            "personalization_score": item.personalization_score,
            "reasons": item.reasons,
            "metadata": item.metadata,
        }
