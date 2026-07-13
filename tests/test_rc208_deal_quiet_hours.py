from app.domains.deal_notifications.service import QuietHoursService


def test_rc208_overnight_quiet_hours():
    service = QuietHoursService()

    at_23 = service.is_quiet_time(
        at_time="2026-07-12T23:00:00+03:00",
        start_time="22:00",
        end_time="08:00",
    )
    at_12 = service.is_quiet_time(
        at_time="2026-07-12T12:00:00+03:00",
        start_time="22:00",
        end_time="08:00",
    )

    assert at_23["quiet"] is True
    assert at_12["quiet"] is False
