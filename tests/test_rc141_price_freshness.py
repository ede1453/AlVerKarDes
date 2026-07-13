from app.domains.commerce_ingestion.price_quality import PriceFreshnessService


def test_rc141_fresh_price():
    result = PriceFreshnessService().evaluate(
        observed_at="2026-07-10T10:00:00+00:00",
        reference_time="2026-07-10T20:00:00+00:00",
    )
    assert result["status"] == "FRESH"
    assert result["usable"] is True

def test_rc141_stale_price():
    result = PriceFreshnessService().evaluate(
        observed_at="2026-07-01T10:00:00+00:00",
        reference_time="2026-07-10T20:00:00+00:00",
    )
    assert result["status"] == "STALE"
    assert result["usable"] is False
