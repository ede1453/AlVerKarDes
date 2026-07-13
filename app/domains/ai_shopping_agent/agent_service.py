from app.domains.ai_shopping_agent.agent_engine import AIShoppingAgentEngine
from app.domains.ai_shopping_agent.agent_models import ShoppingAgentDecision, create_agent_run_id
from app.domains.ai_shopping_agent.agent_serializer import serialize_agent_decision
from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.events.event_bus_service import EventBusService
from app.domains.personalization.personalization_service import PersonalizationService
from app.domains.price_history.price_history_service import PriceHistoryService
from app.domains.product_matching.product_matching_service import ProductMatchingService
from app.domains.unified_search.unified_search_service import UnifiedSearchService


class AIShoppingAgentService:
    def __init__(
        self,
        engine: AIShoppingAgentEngine | None = None,
        search_service: UnifiedSearchService | None = None,
        matching_service: ProductMatchingService | None = None,
        price_history_service: PriceHistoryService | None = None,
        personalization_service: PersonalizationService | None = None,
        cache_service: CacheService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.engine = engine or AIShoppingAgentEngine()
        self.search_service = search_service or UnifiedSearchService()
        self.matching_service = matching_service or ProductMatchingService()
        self.price_history_service = price_history_service or PriceHistoryService()
        self.personalization_service = personalization_service or PersonalizationService()
        self.cache_service = cache_service or CacheService()
        self.event_bus_service = event_bus_service or EventBusService()
        self.key_builder = CacheKeyBuilder()

    def run(self, payload: dict):
        query = payload["query"]
        user_id = payload.get("user_id")
        offers = payload.get("offers", [])

        search = self.search_service.search(
            {
                "query": query,
                "user_id": user_id,
                "marketplaces": payload.get("marketplaces", []),
                "offers": offers,
                "metadata": {"agent_run": True},
            }
        )

        matching = self.matching_service.match(
            {
                "query": query,
                "offers": search["aggregation"]["offers"],
            }
        )

        product_key = None
        if matching["groups"]:
            product_key = matching["groups"][0]["normalized_canonical_name"]

        price_history = None
        if product_key:
            for group in matching["groups"][:1]:
                for candidate in group["candidates"]:
                    self.price_history_service.add_point(
                        {
                            "product_key": product_key,
                            "marketplace": candidate["marketplace"],
                            "price": candidate["price"],
                            "currency": candidate["currency"],
                        }
                    )
            price_history = self.price_history_service.summary(product_key)

        personalization = None
        if user_id:
            if payload.get("profile"):
                profile_payload = dict(payload["profile"])
                profile_payload["user_id"] = user_id
                self.personalization_service.upsert_profile(profile_payload)

            personalization = self.personalization_service.score(
                {
                    "user_id": user_id,
                    "offers": search["aggregation"]["offers"],
                }
            )

        decision_data = self.engine.decide(
            query=query,
            user_id=user_id,
            search=search,
            matching=matching,
            price_history=price_history,
            personalization=personalization,
        )

        decision = ShoppingAgentDecision(
            agent_run_id=create_agent_run_id(),
            user_id=user_id,
            query=query,
            decision=decision_data["decision"],
            confidence=decision_data["confidence"],
            top_offer=decision_data["top_offer"],
            personalization=personalization,
            search=search,
            matching=matching,
            price_history=price_history,
            reasons=decision_data["reasons"],
            next_actions=decision_data["next_actions"],
            metadata={"agent_version": "ai_shopping_agent_v1"},
        )

        serialized = serialize_agent_decision(decision)

        self.event_bus_service.publish(
            {
                "event_type": "ai_shopping_agent.completed",
                "source": "ai_shopping_agent",
                "payload": {
                    "agent_run_id": serialized["agent_run_id"],
                    "query": serialized["query"],
                    "decision": serialized["decision"],
                    "confidence": serialized["confidence"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def run_cached(self, payload: dict):
        cache_key = self.key_builder.build(
            namespace="ai_shopping_agent",
            payload={
                "query": payload["query"],
                "user_id": payload.get("user_id"),
                "offers": payload.get("offers", []),
                "profile": payload.get("profile"),
            },
        )

        return self.cache_service.get_or_set(
            key=cache_key,
            value_factory=lambda: self.run(payload),
            ttl_seconds=payload.get("ttl_seconds", 300),
        )
