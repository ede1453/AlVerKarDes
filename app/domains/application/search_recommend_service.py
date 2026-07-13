from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.connectors.ingestion_service import ConnectorIngestionService
from app.domains.connectors.manager import ConnectorManager
from app.domains.recommendations.service import RecommendationService


@dataclass
class SearchRecommendResult:
    query: str
    country: str
    ingestion: dict
    selected_offer_id: str | None
    recommendation: dict | None
    status: str
    error: str | None = None


class SearchRecommendService:
    def __init__(self, db: AsyncSession, manager: ConnectorManager):
        self.db = db
        self.manager = manager
        self.ingestion_service = ConnectorIngestionService(db=db, manager=manager)
        self.recommendation_service = RecommendationService(db)

    async def run(self, query: str, country: str = "DE", user_context: dict | None = None) -> SearchRecommendResult:
        user_context = user_context or {}

        ingestion = await self.ingestion_service.search_and_ingest(query=query, country=country)

        ingested_items = [item for item in ingestion.items if item.status == "INGESTED" and item.offer_id]

        if not ingested_items:
            return SearchRecommendResult(
                query=query,
                country=country,
                ingestion=self._ingestion_to_dict(ingestion),
                selected_offer_id=None,
                recommendation=None,
                status="NO_INGESTED_OFFERS",
                error="No connector offer could be ingested.",
            )

        selected = self._select_best_item(ingested_items)

        recommendation = await self.recommendation_service.analyze(
            product_url=None,
            product_name=query,
            offer_id=selected.offer_id,
            user_context={
                "country": country,
                "currency": user_context.get("currency", "EUR"),
                "store_name": selected.source,
                "store_trust_score": user_context.get("store_trust_score", 80),
                "reviews": user_context.get("reviews", []),
            },
        )

        return SearchRecommendResult(
            query=query,
            country=country,
            ingestion=self._ingestion_to_dict(ingestion),
            selected_offer_id=selected.offer_id,
            recommendation=recommendation,
            status="OK",
        )

    def _select_best_item(self, items):
        # v0.1: choose first ingested item. The ingestion manager already sorts offers by price/confidence.
        return items[0]

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
