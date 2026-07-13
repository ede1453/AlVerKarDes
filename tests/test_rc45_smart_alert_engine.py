from app.domains.smart_alerts.smart_alert_engine import SmartAlertEngine


def test_smart_alert_engine_triggers_high_alert():
    result = SmartAlertEngine().decide(
        user_id="user-1",
        product_key="macbook-air",
        deal_detection={"deal_level": "EXCELLENT_DEAL", "deal_score": 95},
        price_prediction={"recommendation_hint": "BUY_SOON"},
        personalization={"top_offer": {"personalization_score": 95}},
        channels=["email", "in_app"],
    )

    assert result["should_alert"] is True
    assert result["alert_level"] in ["HIGH", "URGENT"]
    assert result["alert_score"] >= 70


def test_smart_alert_engine_does_not_alert_weak_signal():
    result = SmartAlertEngine().decide(
        user_id="user-1",
        product_key="macbook-air",
        deal_detection={"deal_level": "WEAK_DEAL", "deal_score": 30},
        price_prediction={"recommendation_hint": "WAIT_OR_WATCH"},
        personalization={"top_offer": {"personalization_score": 30}},
    )

    assert result["should_alert"] is False
    assert result["alert_level"] == "NONE"
