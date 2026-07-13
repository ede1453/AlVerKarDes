from app.domains.deal_detection.deal_detection_service import DealDetectionService
from app.domains.events.event_repository_factory import reset_event_repository


def test_deal_detection_service_emits_event():
    reset_event_repository()
    service = DealDetectionService()

    result = service.detect(
        {
            "product_key": "macbook-air",
            "offer": {"price": "949.00", "marketplace": "saturn"},
            "price_history": {"min_price": "949.00", "average_price": "999.00", "latest_price": "949.00", "trend": "DOWN"},
            "personalization": {"top_offer": {"personalization_score": 95}},
        }
    )

    assert result["deal_level"] == "EXCELLENT_DEAL"

    events = service.event_bus_service.list_recent({"event_type": "deal_detection.completed", "source": "deal_detection"})
    assert events


def test_deal_detection_service_cache_hit_on_second_call():
    service = DealDetectionService()
    payload = {
        "product_key": "macbook-air",
        "offer": {"price": "949.00", "marketplace": "saturn"},
        "ttl_seconds": 300,
    }

    first = service.detect_cached(payload)
    second = service.detect_cached(payload)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
