from app.domains.deal_notifications.service import NotificationChannelRouter


def test_rc209_quiet_nonurgent_deferred():
    result = NotificationChannelRouter().route(
        enabled_channels=["in_app","push","sms"],
        quiet=True,
        urgent=False,
    )
    assert result["immediate_channels"] == []
    assert result["deferred_channels"] == ["in_app","push"]
    assert result["dropped_channels"] == ["sms"]

def test_rc209_urgent_bypasses_quiet_hours():
    result = NotificationChannelRouter().route(
        enabled_channels=["push"],
        quiet=True,
        urgent=True,
    )
    assert result["immediate_channels"] == ["push"]
