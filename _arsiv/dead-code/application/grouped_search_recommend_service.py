from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.application.grouped_merge_presenter import GroupedMergePresenter
from app.domains.connectors.ingestion_service import ConnectorIngestionService
from app.domains.connectors.manager import ConnectorManager
from app.domains.connectors.search_presenter import ConnectorSearchPresenter
from app.domains.decision.consumer_decision_engine import ConsumerDecisionEngine
from app.domains.decision.decision_input_builder import DecisionInputBuilder
from app.domains.products.merge_aware_ingestion import MergeAwareIngestionPlanner
from app.domains.recommendations.service import RecommendationService


@dataclass
class GroupedSearchRecommendResult:
    query: str
    country: str
    search: dict
    ingestion: dict
    selected_group_id: str | None
    selected_offer_id: str | None
    recommendation: dict | None
    status: str
    error: str | None = None
    consumer_decision: dict | None = None


class GroupedSearchRecommendService:
    def __init__(self, db: AsyncSession, manager: ConnectorManager):
        self.db = db
        self.manager = manager
        self.ingestion_service = ConnectorIngestionService(db=db, manager=manager)
        self.recommendation_service = RecommendationService(db)
        self.presenter = ConnectorSearchPresenter()
        self.merge_presenter = GroupedMergePresenter()
        self.merge_aware_planner = MergeAwareIngestionPlanner()
        self.decision_engine = ConsumerDecisionEngine()
        self.decision_input_builder = DecisionInputBuilder()

    async def run(self, query: str, country: str = "DE", user_context: dict | None = None) -> GroupedSearchRecommendResult:
        user_context = user_context or {}
        search_result = await self.manager.search_all(query=query, country=country)
        search_payload = self.presenter.present(
            query=search_result.query,
            country=search_result.country,
            offers=search_result.offers,
            errors=search_result.errors,
        )

        selected_group = self._select_best_group(search_payload)
        if not selected_group:
            return GroupedSearchRecommendResult(query, country, search_payload, {}, None, None, None, "NO_GROUPS", "No product group found.", None)

        ingestion = await self.ingestion_service.search_and_ingest(query=query, country=country)
        ingestion_payload = self._ingestion_to_dict(ingestion)

        search_payload = self.merge_presenter.attach_merge_plans(search_payload=search_payload, ingestion_payload=ingestion_payload)
        search_payload = self.merge_aware_planner.apply_to_response(search_payload=search_payload, ingestion_payload=ingestion_payload)
        selected_group = self._select_best_group(search_payload)

        selected_ingested_item = self._select_ingested_item_for_best_offer(selected_group=selected_group, ingestion_payload=ingestion_payload)
        if not selected_ingested_item:
            return GroupedSearchRecommendResult(query, country, search_payload, ingestion_payload, selected_group.get("match_group_id"), None, None, "NO_INGESTED_BEST_OFFER", "Best offer could not be matched to an ingested offer.", None)

        recommendation = await self.recommendation_service.analyze(
            product_url=selected_group["best_offer"].get("url"),
            product_name=selected_group.get("representative_title") or query,
            offer_id=selected_ingested_item["offer_id"],
            user_context={
                "country": country,
                "currency": user_context.get("currency", "EUR"),
                "store_name": selected_group["best_offer"].get("source"),
                "store_trust_score": user_context.get("store_trust_score", 80),
                "reviews": user_context.get("reviews", []),
                "search_group": selected_group,
            },
        )

        decision_input = self.decision_input_builder.from_grouped_recommendation(
            selected_group=selected_group,
            recommendation=recommendation,
            user_context=user_context,
        )
        decision = self.decision_engine.decide(decision_input)
        consumer_decision = {
            "decision": decision.decision,
            "score": decision.score,
            "confidence": decision.confidence,
            "reasons": decision.reasons,
            "risks": decision.risks,
            "recommended_action": decision.recommended_action,
            "signals": decision.signals,
        }

        return GroupedSearchRecommendResult(
            query=query,
            country=country,
            search=search_payload,
            ingestion=ingestion_payload,
            selected_group_id=selected_group.get("match_group_id"),
            selected_offer_id=selected_ingested_item["offer_id"],
            recommendation=recommendation,
            consumer_decision=consumer_decision,
            status="OK",
        )

    def _select_best_group(self, search_payload: dict) -> dict | None:
        groups = search_payload.get("groups", [])
        return groups[0] if groups else None

    def _select_ingested_item_for_best_offer(self, *, selected_group: dict, ingestion_payload: dict) -> dict | None:
        best_source = (selected_group.get("best_offer") or {}).get("source")
        for item in ingestion_payload.get("items", []):
            if item.get("status") == "INGESTED" and item.get("source") == best_source:
                return item
        ingested = [item for item in ingestion_payload.get("items", []) if item.get("status") == "INGESTED" and item.get("offer_id")]
        return ingested[0] if ingested else None

    def _ingestion_to_dict(self, ingestion) -> dict:
        return {
            "query": ingestion.query,
            "country": ingestion.country,
            "total_offers": ingestion.total_offers,
            "ingested_count": ingestion.ingested_count,
            "skipped_count": ingestion.skipped_count,
            "items": [item.__dict__ for item in ingestion.items],
            "connector_errors": ingestion.connector_errors,
        }
