from app.domains.discount_intelligence.discount_service import DiscountIntelligenceService
from app.domains.events.event_repository_factory import reset_event_repository


def test_discount_service_emits_event():
    reset_event_repository()
    service = DiscountIntelligenceService()

    result = service.analyze(
        {
            "product_key": "macbook-air",
            "current_price": "949.00",
            "claimed_original_price": "1099.00",
            "price_history": {"min_price": "949.00", "average_price": "999.00", "max_price": "1099.00", "trend": "DOWN"},
            "deal_detection": {"deal_score": 95},
            "price_prediction": {"recommendation_hint": "BUY_SOON"},
        }
    )

    assert result["discount_quality"] == "EXCELLENT_REAL_DISCOUNT"

    events = service.event_bus_service.list_recent(
        {"event_type": "discount_intelligence.analyzed", "source": "discount_intelligence"}
    )
    assert events


def test_discount_service_cache_hit_on_second_call():
    service = DiscountIntelligenceService()
    payload = {
        "product_key": "macbook-air",
        "current_price": "949.00",
        "claimed_original_price": "1099.00",
        "ttl_seconds": 300,
    }

    first = service.analyze_cached(payload)
    second = service.analyze_cached(payload)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
