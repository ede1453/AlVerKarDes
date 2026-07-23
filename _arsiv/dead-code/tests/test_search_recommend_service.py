import pytest

from app.domains.application.search_recommend_service import SearchRecommendService
from app.domains.connectors.ingestion_service import ConnectorIngestionResult, IngestedOfferResult


class DummyDB:
    pass


class DummyManager:
    pass


class FakeIngestionService:
    async def search_and_ingest(self, query: str, country: str = "DE"):
        return ConnectorIngestionResult(
            query=query,
            country=country,
            total_offers=1,
            ingested_count=1,
            skipped_count=0,
            items=[
                IngestedOfferResult(
                    source="mock-amazon-de",
                    title="Apple MacBook Air M5 16GB 512GB",
                    canonical_key="apple::macbook-air::m5::16gb::512gb::de",
                    product_id="11111111-1111-1111-1111-111111111111",
                    store_id="22222222-2222-2222-2222-222222222222",
                    offer_id="33333333-3333-3333-3333-333333333333",
                    price_id="44444444-4444-4444-4444-444444444444",
                    status="INGESTED",
                )
            ],
        )


class FakeRecommendationService:
    async def analyze(self, product_url, product_name, offer_id, user_context):
        return {
            "decision": "BUY",
            "confidence": 80,
            "offer_id": str(offer_id),
            "summary": "Test recommendation.",
        }


@pytest.mark.asyncio
async def test_search_recommend_ok():
    service = SearchRecommendService(db=DummyDB(), manager=DummyManager())
    service.ingestion_service = FakeIngestionService()
    service.recommendation_service = FakeRecommendationService()

    result = await service.run("Apple MacBook Air M5 16GB 512GB")

    assert result.status == "OK"
    assert result.selected_offer_id == "33333333-3333-3333-3333-333333333333"
    assert result.recommendation["decision"] == "BUY"


class EmptyIngestionService:
    async def search_and_ingest(self, query: str, country: str = "DE"):
        return ConnectorIngestionResult(
            query=query,
            country=country,
            total_offers=0,
            ingested_count=0,
            skipped_count=0,
            items=[],
        )


@pytest.mark.asyncio
async def test_search_recommend_no_offers():
    service = SearchRecommendService(db=DummyDB(), manager=DummyManager())
    service.ingestion_service = EmptyIngestionService()
    service.recommendation_service = FakeRecommendationService()

    result = await service.run("Unknown Product")

    assert result.status == "NO_INGESTED_OFFERS"
    assert result.recommendation is None
