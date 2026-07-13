from app.domains.deal_intelligence.service import DiscountTruthEngine


def test_rc146_genuine_discount():
    result = DiscountTruthEngine().verify(
        current_price=700,
        claimed_original_price=1000,
        historical_prices=[950, 1000, 1050, 980],
    )
    assert result["verified"] is True
    assert result["truth_status"] == "GENUINE_STRONG_DISCOUNT"

def test_rc146_misleading_discount():
    result = DiscountTruthEngine().verify(
        current_price=950,
        claimed_original_price=1500,
        historical_prices=[950, 960, 970, 940],
    )
    assert result["verified"] is False
    assert result["truth_status"] == "POSSIBLY_MISLEADING_DISCOUNT"
