import pytest

from app.domains.application.grouped_search_recommend_service import GroupedSearchRecommendService
from app.domains.connectors.ingestion_service import ConnectorIngestionResult, IngestedOfferResult


class DummyDB:
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
                        "availability": "in_stock",
                        "match_group_score": 100,
                    },
                    "confidence": {"best_match_group_score": 100},
                    "offers": [{"source": "mock-amazon-de", "overall_confidence": 90}],
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
            "recommendation_id": "rec-1",
            "summary": "ok",
            "evidence": [
                {
                    "type": "PRICE_HISTORY",
                    "confidence": 80,
                    "data": {"current_price": 849, "historical_lowest": 849, "historical_average": 999},
                },
                {"type": "FRAUD_ANALYSIS", "data": {"risk_level": "LOW"}},
            ],
            "agent_trace": {
                "price_intelligence": {"price_signal": "BUY", "confidence": 80},
                "fraud_agent": {"risk_level": "LOW"},
                "review_analyst": {"review_reliability": "LOW"},
            },
        }


class NoopMergePresenter:
    def attach_merge_plans(self, *, search_payload, ingestion_payload):
        return search_payload


class NoopMergeAwarePlanner:
    def apply_to_response(self, *, search_payload, ingestion_payload):
        return search_payload


@pytest.mark.asyncio
async def test_grouped_search_recommend_adds_consumer_decision():
    service = GroupedSearchRecommendService(db=DummyDB(), manager=FakeManager())
    service.presenter = FakePresenter()
    service.ingestion_service = FakeIngestionService()
    service.recommendation_service = FakeRecommendationService()
    service.merge_presenter = NoopMergePresenter()
    service.merge_aware_planner = NoopMergeAwarePlanner()

    result = await service.run("M5", user_context={"store_trust_score": 90})

    assert result.status == "OK"
    assert result.consumer_decision is not None
    assert result.consumer_decision["decision"] == "BUY_NOW"
    assert result.consumer_decision["score"] >= 75