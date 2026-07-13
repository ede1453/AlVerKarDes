from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.user_activity.activity_service import UserActivityService


def test_user_activity_service_records_and_emits_event():
    reset_event_repository()
    service = UserActivityService()

    event = service.record(
        {
            "user_id": "user-1",
            "event_type": "recommendation_clicked",
            "product_key": "macbook-air",
        }
    )

    assert event["event_type"] == "recommendation_clicked"

    events = service.event_bus_service.list_recent(
        {"event_type": "user_activity.recorded", "source": "user_activity"}
    )
    assert events


def test_user_activity_service_summary_and_adjustment():
    service = UserActivityService()
    service.record({"user_id": "user-1", "event_type": "liked", "product_key": "macbook-air"})
    service.record({"user_id": "user-1", "event_type": "disliked", "product_key": "iphone"})

    summary = service.summarize("user-1")
    assert summary["preferred_product_keys"] == ["macbook-air"]

    adjusted = service.adjust_recommendations(
        {
            "user_id": "user-1",
            "recommendations": [
                {"product_key": "iphone", "product_name": "iPhone", "score": 80, "rationale": []},
                {"product_key": "macbook-air", "product_name": "MacBook Air", "score": 75, "rationale": []},
            ],
        }
    )

    assert adjusted["items"][0]["product_key"] == "macbook-air"
