from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.smart_alerts.smart_alert_service import SmartAlertService


def test_smart_alert_service_emits_event():
    reset_event_repository()
    service = SmartAlertService()

    result = service.evaluate(
        {
            "user_id": "user-1",
            "product_key": "macbook-air",
            "deal_detection": {"deal_level": "EXCELLENT_DEAL", "deal_score": 95},
            "price_prediction": {"recommendation_hint": "BUY_SOON"},
            "personalization": {"top_offer": {"personalization_score": 95}},
            "channels": ["in_app"],
        }
    )

    assert result["should_alert"] is True

    events = service.event_bus_service.list_recent({"event_type": "smart_alert.evaluated", "source": "smart_alerts"})
    assert events


def test_smart_alert_service_cache_hit_on_second_call():
    service = SmartAlertService()
    payload = {
        "user_id": "user-1",
        "product_key": "macbook-air",
        "deal_detection": {"deal_level": "GOOD_DEAL", "deal_score": 80},
        "ttl_seconds": 300,
    }

    first = service.evaluate_cached(payload)
    second = service.evaluate_cached(payload)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
