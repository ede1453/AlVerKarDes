from app.domains.ai_explanation.explanation_service import AIExplanationService
from app.domains.deal_detection.deal_detection_service import DealDetectionService
from app.domains.discount_intelligence.discount_service import DiscountIntelligenceService
from app.domains.events.event_bus_service import EventBusService
from app.domains.marketplace_aggregation.marketplace_service import MarketplaceAggregationService
from app.domains.notifications.notification_service import NotificationService
from app.domains.price_prediction.price_prediction_service import PricePredictionService
from app.domains.product_canonicalization.canonical_service import ProductCanonicalizationService
from app.domains.profile_aware_recommendations.profile_aware_service import ProfileAwareRecommendationService
from app.domains.shopping_pipeline.pipeline_models import ShoppingPipelineResult, create_pipeline_id
from app.domains.shopping_pipeline.pipeline_serializer import serialize_pipeline_result
from app.domains.smart_alerts.smart_alert_service import SmartAlertService


class ShoppingPipelineService:
    def __init__(
        self,
        marketplace_service: MarketplaceAggregationService | None = None,
        canonicalization_service: ProductCanonicalizationService | None = None,
        recommendation_service: ProfileAwareRecommendationService | None = None,
        deal_service: DealDetectionService | None = None,
        prediction_service: PricePredictionService | None = None,
        discount_service: DiscountIntelligenceService | None = None,
        alert_service: SmartAlertService | None = None,
        explanation_service: AIExplanationService | None = None,
        notification_service: NotificationService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.marketplace_service = marketplace_service or MarketplaceAggregationService()
        self.canonicalization_service = canonicalization_service or ProductCanonicalizationService()
        self.recommendation_service = recommendation_service or ProfileAwareRecommendationService()
        self.deal_service = deal_service or DealDetectionService()
        self.prediction_service = prediction_service or PricePredictionService()
        self.discount_service = discount_service or DiscountIntelligenceService()
        self.alert_service = alert_service or SmartAlertService()
        self.explanation_service = explanation_service or AIExplanationService()
        self.notification_service = notification_service or NotificationService()
        self.event_bus_service = event_bus_service or EventBusService()

    def run(self, payload: dict):
        user_id = payload["user_id"]
        query = payload["query"]
        offers = payload.get("offers") or self._default_offers(query)

        search = self.marketplace_service.aggregate(
            {
                "query": query,
                "offers": offers,
            }
        )

        canonicalization = self.canonicalization_service.canonicalize(
            {
                "query": query,
                "offers": search.get("offers", []),
            }
        )

        candidates = self._candidates_from_canonicalization(
            canonicalization=canonicalization,
            offers=search.get("offers", []),
        )

        recommendation = self.recommendation_service.recommend(
            {
                "user_id": user_id,
                "query": query,
                "candidates": candidates,
                "profile_context": payload.get("profile_context"),
                "personalization": payload.get("personalization"),
                "deal_detection": payload.get("deal_detection"),
                "discount_intelligence": payload.get("discount_intelligence"),
                "price_prediction": payload.get("price_prediction"),
            }
        )

        top = recommendation.get("items", [None])[0] if recommendation.get("items") else None

        price_history = payload.get("price_history") or self._price_history_from_search(search)
        deal_detection = None
        price_prediction = None
        discount_intelligence = None
        smart_alert = None
        explanation = None
        notification = None

        if top:
            top_price = self._extract_price(top)
            top_marketplace = self._extract_marketplace(top)

            deal_detection = self.deal_service.detect(
                {
                    "product_key": top.get("product_key") or query.lower().replace(" ", "-"),
                    "offer": {
                        "price": top_price,
                        "marketplace": top_marketplace,
                    },
                    "price_history": price_history,
                    "personalization": {
                        "top_offer": {
                            "personalization_score": top.get("score", 50),
                        }
                    },
                }
            )

            price_prediction = self.prediction_service.predict(
                {
                    "product_key": top.get("product_key") or query.lower().replace(" ", "-"),
                    "price_history": price_history,
                    "prediction_horizon_days": payload.get("prediction_horizon_days", 7),
                }
            )

            discount_intelligence = self.discount_service.analyze(
                {
                    "product_key": top.get("product_key") or query.lower().replace(" ", "-"),
                    "current_price": top_price,
                    "claimed_original_price": payload.get("claimed_original_price"),
                    "price_history": price_history,
                    "deal_detection": deal_detection,
                    "price_prediction": price_prediction,
                }
            )

            smart_alert = self.alert_service.evaluate(
                {
                    "user_id": user_id,
                    "product_key": top.get("product_key") or query.lower().replace(" ", "-"),
                    "deal_detection": deal_detection,
                    "price_prediction": price_prediction,
                    "personalization": {
                        "top_offer": {
                            "personalization_score": top.get("score", 50),
                        }
                    },
                    "channels": payload.get("channels") or ["in_app"],
                }
            )

            explanation = self.explanation_service.explain(
                {
                    "language": payload.get("language", "en"),
                    "tone": payload.get("tone", "clear"),
                    "agent_decision": {"decision": "BUY_NOW" if top.get("score", 0) >= 70 else "CONSIDER"},
                    "deal_detection": deal_detection,
                    "discount_intelligence": discount_intelligence,
                    "smart_alert": smart_alert,
                    "price_prediction": price_prediction,
                }
            )

            if payload.get("deliver_notification", False) and smart_alert and smart_alert.get("should_alert"):
                notification = self.notification_service.deliver_from_smart_alert(
                    {
                        "user_id": user_id,
                        "smart_alert": smart_alert,
                        "provider": payload.get("notification_provider", "mock"),
                    }
                )

        result = ShoppingPipelineResult(
            pipeline_id=create_pipeline_id(),
            user_id=user_id,
            query=query,
            status="COMPLETED" if top else "NO_RECOMMENDATION",
            top_recommendation=top,
            search=search,
            canonicalization=canonicalization,
            recommendation=recommendation,
            deal_detection=deal_detection,
            price_prediction=price_prediction,
            discount_intelligence=discount_intelligence,
            smart_alert=smart_alert,
            explanation=explanation,
            notification=notification,
            metadata={"shopping_pipeline_version": "shopping_pipeline_v1"},
        )

        serialized = serialize_pipeline_result(result)

        self.event_bus_service.publish(
            {
                "event_type": "shopping_pipeline.completed",
                "source": "shopping_pipeline",
                "payload": {
                    "pipeline_id": serialized["pipeline_id"],
                    "user_id": user_id,
                    "query": query,
                    "status": serialized["status"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def _default_offers(self, query: str):
        return [
            {
                "marketplace": "saturn",
                "seller": "Saturn",
                "product_name": f"Apple {query}",
                "price": "949.00",
                "currency": "EUR",
            },
            {
                "marketplace": "amazon",
                "seller": "Amazon",
                "product_name": f"Apple {query}",
                "price": "999.00",
                "currency": "EUR",
            },
        ]

    def _candidates_from_canonicalization(self, *, canonicalization: dict, offers: list[dict]):
        candidates = []
        first_price_by_name = {}
        marketplace_by_name = {}
        for offer in offers:
            name = offer.get("product_name")
            if name and name not in first_price_by_name:
                first_price_by_name[name] = offer.get("price")
                marketplace_by_name[name] = offer.get("marketplace")

        for product in canonicalization.get("products", []):
            candidates.append(
                {
                    "product_key": product.get("canonical_key"),
                    "product_name": product.get("product_name"),
                    "marketplace": marketplace_by_name.get(product.get("product_name")) or "saturn",
                    "price": first_price_by_name.get(product.get("product_name")) or "949.00",
                    "canonical_confidence": product.get("confidence", 50),
                    "source": product,
                }
            )

        return candidates

    def _price_history_from_search(self, search: dict):
        prices = [float(offer["price"]) for offer in search.get("offers", []) if offer.get("price") is not None]
        if not prices:
            prices = [949.00]
        latest = min(prices)
        return {
            "latest_price": f"{latest:.2f}",
            "min_price": f"{min(prices):.2f}",
            "average_price": f"{(sum(prices) / len(prices)):.2f}",
            "max_price": f"{max(prices):.2f}",
            "trend": "DOWN" if len(prices) > 1 and min(prices) < max(prices) else "FLAT",
            "points": [{"price": f"{price:.2f}"} for price in prices],
        }

    def _extract_price(self, top: dict):
        return str(top.get("source", {}).get("price") or top.get("price") or "949.00")

    def _extract_marketplace(self, top: dict):
        return top.get("source", {}).get("marketplace") or top.get("marketplace") or "saturn"
