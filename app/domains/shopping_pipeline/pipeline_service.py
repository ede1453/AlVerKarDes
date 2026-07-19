from app.domains.ai_explanation.explanation_service import AIExplanationService
from app.domains.deal_detection.deal_detection_service import DealDetectionService
from app.domains.discount_intelligence.discount_service import DiscountIntelligenceService
from app.domains.events.event_bus_service import EventBusService
from app.domains.market.service import MarketService
from app.domains.marketplace_aggregation.marketplace_service import MarketplaceAggregationService
from app.domains.notifications.notification_service import NotificationService
from app.domains.price_prediction.price_prediction_service import PricePredictionService
from app.domains.products.canonical_service import CanonicalProductService
from app.domains.products.repository import ProductRepository
from app.domains.products.service import ProductService
from app.domains.profile_aware_recommendations.profile_aware_service import ProfileAwareRecommendationService
from app.domains.shopping_pipeline.pipeline_models import ShoppingPipelineResult, create_pipeline_id
from app.domains.shopping_pipeline.pipeline_serializer import serialize_pipeline_result
from app.domains.smart_alerts.smart_alert_service import SmartAlertService


class ShoppingPipelineService:
    def __init__(
        self,
        marketplace_service: MarketplaceAggregationService | None = None,
        canonicalization_service: CanonicalProductService | None = None,
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
        self.canonicalization_service = canonicalization_service or CanonicalProductService()
        self.recommendation_service = recommendation_service or ProfileAwareRecommendationService()
        self.deal_service = deal_service or DealDetectionService()
        self.prediction_service = prediction_service or PricePredictionService()
        self.discount_service = discount_service or DiscountIntelligenceService()
        self.alert_service = alert_service or SmartAlertService()
        self.explanation_service = explanation_service or AIExplanationService()
        self.notification_service = notification_service or NotificationService()
        self.event_bus_service = event_bus_service or EventBusService()

    async def run(self, payload: dict, db):
        user_id = payload["user_id"]
        query = payload["query"]
        offers = payload.get("offers") or await self._real_offers(db, query)

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

        price_history = None
        deal_detection = None
        price_prediction = None
        discount_intelligence = None
        smart_alert = None
        explanation = None
        notification = None

        if top:
            # CONNECT-001: price_history used to be fabricated from the
            # current search's offers (min/max/avg of *today's* prices, with
            # a hardcoded 949.00 fallback when even that was empty) -- never
            # a real historical read, so deal_detection/price_prediction/
            # discount_intelligence for this pipeline's primary user-facing
            # flow never reflected actual history. Explicit caller-supplied
            # price_history (e.g. tests) is still honored as-is; otherwise
            # this reads the real market.Price table via the product's
            # canonical_key, and returns an explicit INSUFFICIENT_DATA
            # status (not fabricated numbers) when no real history exists.
            # CONNECT-003: top["product_key"] now comes from
            # CanonicalProductService (the real ingestion-path normalizer),
            # so it can be trusted directly -- no need to re-derive it from
            # product_name via a second normalization pass as CONNECT-001
            # had to (that was a workaround for canonicalization's old
            # mismatch with the real engine, now fixed at the source).
            price_history = payload.get("price_history")
            if price_history is None:
                price_history = await self._real_price_history(db, top.get("product_key"))

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
            price_history=price_history,
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

    async def _real_offers(self, db, query: str):
        """CLIENT-000b: eskiden burada _default_offers() vardı -- offers
        hiç verilmediginde hardcoded "Apple {query}" @ Saturn 949.00 /
        Amazon 999.00 dondururdu, gercek ingestion'a hic baglanmamisti
        (CONNECT-001'in price_history icin temizledigi ayni fabrikasyon,
        arama adiminda hayatta kalmisti -- bkz. WIKI_ROOT risk kaydi
        Shopping-Pipeline-Sahte-Arama-Verisi-CLIENT-000).

        Artik gercekten ingest edilmis urunleri arayip (ProductService,
        GET /products/search ile ayni motor) gercek teklif+fiyat
        cifitlerini donduruyor. Eslesen urun yoksa BOS liste doner --
        sahte bir teklif uydurmaz; asagidaki pipeline akisi bunu
        top=None -> status="NO_RECOMMENDATION" olarak dogru sekilde
        isaretler (949.00 gibi uydurma bir sayi asla uretilmez)."""
        products = await ProductService(db).search_products(query, limit=5)
        if not products:
            return []

        offers: list[dict] = []
        for product in products:
            pairs = await MarketService(db).get_offers_with_latest_price_for_product(product.id)
            for item in pairs:
                offer, store, price = item["offer"], item["store"], item["price"]
                offers.append(
                    {
                        "marketplace": store.name,
                        "seller": store.name,
                        "product_name": product.title,
                        "price": str(price.amount),
                        "currency": price.currency,
                        "url": offer.url,
                        "availability": price.stock_status or "UNKNOWN",
                        "metadata": {
                            "is_real_data": price.metadata_json.get("is_real_data", True),
                            "offer_id": str(offer.id),
                        },
                    }
                )
        return offers

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

    async def _real_price_history(self, db, canonical_key: str | None) -> dict:
        """CONNECT-001: reads real price history from market.Price (the
        canonical store, see ADR-007 Karar 3) via the product's
        canonical_key. Returns an explicit INSUFFICIENT_DATA status instead
        of fabricating numbers when no real data exists -- consistent with
        this project's "don't let missing/unreliable data produce a
        definitive decision" discipline (already applied elsewhere, e.g.
        AUTH-003 Part 2's refusal to invent ownership data).

        CONNECT-003: canonical_key is now trusted directly from this
        pipeline's own canonicalization step (CanonicalProductService, the
        real ingestion-path engine) rather than re-derived from product_name
        here -- CONNECT-001 had to re-derive it because canonicalization
        still used the standalone product_canonicalization domain, which
        produced a DIFFERENT canonical_key format than the real ingestion
        path. That mismatch is fixed at the source now (ADR-007 Karar 2)."""
        if not canonical_key:
            return {"status": "INSUFFICIENT_DATA", "reason": "NO_CANONICAL_KEY"}

        product = await ProductRepository(db).get_by_canonical_key(canonical_key)
        if product is None:
            return {"status": "INSUFFICIENT_DATA", "reason": "PRODUCT_NOT_FOUND"}

        # CLIENT-002b: ozet-hesaplama mantigi MarketService'e tasindi --
        # GET /products/{id}/detail de ayni gercek market.Price verisinden
        # ayni sekilde ozet uretiyor, ikinci bir paralel implementasyon
        # yaratilmadi. Davranis birebir korunuyor (CONNECT-001).
        return await MarketService(db).get_price_history_summary_for_product(product.id)

    def _extract_price(self, top: dict):
        return str(top.get("source", {}).get("price") or top.get("price") or "949.00")

    def _extract_marketplace(self, top: dict):
        return top.get("source", {}).get("marketplace") or top.get("marketplace") or "saturn"
