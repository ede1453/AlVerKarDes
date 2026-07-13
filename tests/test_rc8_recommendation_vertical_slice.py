from app.domains.analytics.recommendation_vertical_slice import RecommendationVerticalSlice


def test_vertical_slice_returns_buy_now():
    result = RecommendationVerticalSlice().evaluate(
        deal_score=95,
        authenticity_score=96,
    )

    assert result.recommendation == "BUY_NOW"
    assert result.confidence == 95
    assert result.source == "recommendation_vertical_slice"


def test_vertical_slice_returns_avoid_for_fake_discount():
    result = RecommendationVerticalSlice().evaluate(
        deal_score=99,
        authenticity_score=10,
    )

    assert result.recommendation == "AVOID"
    assert result.reason == "possible_fake_discount"
