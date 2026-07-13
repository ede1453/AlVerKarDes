from app.domains.deal_notifications.provider_governance import NotificationPerformanceService


def test_rc220_performance_summary():
    result = NotificationPerformanceService().summarize(
        delivery_attempts=[
            {"successful":True},
            {"successful":False},
        ],
        engagement_events=[
            {"event_type":"DELIVERED"},
            {"event_type":"OPENED"},
            {"event_type":"CLICKED"},
            {"event_type":"CONVERTED"},
        ],
    )

    assert result["delivery_success_rate"] == 0.5
    assert result["open_rate"] == 1.0
    assert result["click_rate"] == 1.0
    assert result["conversion_rate"] == 1.0
