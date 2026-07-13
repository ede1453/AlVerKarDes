from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.price_prediction.price_prediction_service import PricePredictionService


def test_price_prediction_service_emits_event():
    reset_event_repository()
    service = PricePredictionService()

    result = service.predict(
        {
            "product_key": "macbook-air",
            "price_history": {
                "latest_price": "949.00",
                "min_price": "949.00",
                "average_price": "999.00",
                "max_price": "1099.00",
                "trend": "DOWN",
                "points": [{"price": "999.00"}, {"price": "949.00"}],
            },
        }
    )

    assert result["recommendation_hint"] == "BUY_SOON"

    events = service.event_bus_service.list_recent(
        {"event_type": "price_prediction.completed", "source": "price_prediction"}
    )
    assert events


def test_price_prediction_service_cache_hit_on_second_call():
    service = PricePredictionService()
    payload = {
        "product_key": "macbook-air",
        "price_history": {"latest_price": "949.00", "points": [{"price": "949.00"}]},
        "ttl_seconds": 300,
    }

    first = service.predict_cached(payload)
    second = service.predict_cached(payload)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
