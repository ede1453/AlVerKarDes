from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.watchlist.watchlist_service import WatchlistService


def test_watchlist_service_adds_item_and_emits_event():
    reset_event_repository()
    service = WatchlistService()

    item = service.add_item(
        {
            "user_id": "user-1",
            "product_key": "macbook-air",
            "query": "MacBook Air",
            "target_price": "950.00",
        }
    )

    assert item["status"] == "ACTIVE"

    events = service.event_bus_service.list_recent({"event_type": "watchlist.item_added", "source": "watchlist"})
    assert events


def test_watchlist_service_evaluates_target_and_alert():
    service = WatchlistService()
    item = service.add_item(
        {
            "user_id": "user-1",
            "product_key": "macbook-air",
            "query": "MacBook Air",
            "target_price": "950.00",
        }
    )

    evaluated = service.evaluate_item(
        item["id"],
        {
            "deal_detection": {"deal_level": "EXCELLENT_DEAL", "deal_score": 95},
            "price_prediction": {"recommendation_hint": "BUY_SOON"},
            "personalization": {"top_offer": {"personalization_score": 95}},
            "price_history": {"latest_price": "949.00"},
        },
    )

    assert evaluated["last_evaluation"]["target_reached"] is True
    assert evaluated["last_evaluation"]["smart_alert"]["should_alert"] is True
