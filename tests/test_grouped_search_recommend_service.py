import pytest

from app.domains.application.grouped_search_recommend_service import GroupedSearchRecommendService
from app.domains.connectors.ingestion_service import ConnectorIngestionResult, IngestedOfferResult


class DummyDB:
    pass


class DummyManager:
    pass


class FakePresenter:
    def present(self, *, query, country, offers, errors):
        return {
            "query": query,
            "country": country,
            "group_count": 1,
            "offer_count": 1,
            "groups": [
                {
                    "match_group_id": "group::apple-mba-m5",
                    "representative_title": "Apple MacBook Air M5 16GB 512GB",
                    "best_offer": {
                        "source": "mock-amazon-de",
                        "url": "https://example.com/amazon/macbook",
                        "price": 849,
                    },
                }
            ],
            "errors": [],
        }


class FakeManager:
    async def search_all(self, query: str, country: str = "DE"):
        class Result:
            pass

        result = Result()
        result.query = query
        result.country = country
        result.offers = []
        result.errors = []
        return result


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
            "summary": "Grouped recommendation.",
        }


@pytest.mark.asyncio
async def test_grouped_search_recommend_ok():
    service = GroupedSearchRecommendService(db=DummyDB(), manager=FakeManager())
    service.presenter = FakePresenter()
    service.ingestion_service = FakeIngestionService()
    service.recommendation_service = FakeRecommendationService()

    result = await service.run("M5")

    assert result.status == "OK"
    assert result.selected_group_id == "group::apple-mba-m5"
    assert result.selected_offer_id == "33333333-3333-3333-3333-333333333333"
    assert result.recommendation["decision"] == "BUY"


class EmptyPresenter:
    def present(self, *, query, country, offers, errors):
        return {
            "query": query,
            "country": country,
            "group_count": 0,
            "offer_count": 0,
            "groups": [],
            "errors": [],
        }


@pytest.mark.asyncio
async def test_grouped_search_recommend_no_groups():
    service = GroupedSearchRecommendService(db=DummyDB(), manager=FakeManager())
    service.presenter = EmptyPresenter()
    service.ingestion_service = FakeIngestionService()
    service.recommendation_service = FakeRecommendationService()

    result = await service.run("Unknown")

    assert result.status == "NO_GROUPS"
    assert result.recommendation is None
