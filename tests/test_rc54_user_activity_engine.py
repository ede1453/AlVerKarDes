from app.domains.user_activity.activity_engine import UserActivityEngine
from app.domains.user_activity.activity_models import UserActivityEvent, create_activity_id


def test_user_activity_engine_summarizes_positive_and_negative_signals():
    events = [
        UserActivityEvent(create_activity_id(), "user-1", "recommendation_clicked", product_key="macbook-air"),
        UserActivityEvent(create_activity_id(), "user-1", "liked", product_key="macbook-air"),
        UserActivityEvent(create_activity_id(), "user-1", "not_interested", product_key="iphone"),
    ]

    summary = UserActivityEngine().summarize(user_id="user-1", events=events)

    assert summary["positive_count"] == 2
    assert summary["negative_count"] == 1
    assert summary["preferred_product_keys"] == ["macbook-air"]
    assert summary["avoided_product_keys"] == ["iphone"]


def test_user_activity_engine_adjusts_recommendations():
    result = UserActivityEngine().recommendation_adjustment(
        summary={
            "preferred_product_keys": ["macbook-air"],
            "avoided_product_keys": ["iphone"],
        },
        recommendations=[
            {"product_key": "iphone", "product_name": "iPhone", "score": 80, "rationale": []},
            {"product_key": "macbook-air", "product_name": "MacBook Air", "score": 75, "rationale": []},
        ],
    )

    assert result["items"][0]["product_key"] == "macbook-air"
    assert result["items"][0]["score"] == 85
