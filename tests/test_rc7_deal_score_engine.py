from decimal import Decimal

from app.domains.deals.deal_score_engine import DealScoreEngine, DealScoreInput
from app.domains.deals.deal_score_serializer import serialize_deal_score_result


def test_deal_score_engine_returns_buy_for_strong_deal():
    result = DealScoreEngine().calculate(
        DealScoreInput(
            current_amount=Decimal("849.00"),
            lowest_90d_amount=Decimal("849.00"),
            cross_store_min_amount=Decimal("849.00"),
            store_trust_score=95,
            stock_status="in_stock",
        )
    )

    assert result.score >= 80
    assert result.decision == "BUY"
    assert "at_or_below_historical_low" in result.reasons
    assert "best_cross_store_price" in result.reasons


def test_deal_score_engine_returns_wait_for_bad_deal():
    result = DealScoreEngine().calculate(
        DealScoreInput(
            current_amount=Decimal("999.00"),
            lowest_90d_amount=Decimal("849.00"),
            cross_store_min_amount=Decimal("879.00"),
            store_trust_score=40,
            stock_status="out_of_stock",
        )
    )

    assert result.score < 60
    assert result.decision == "WAIT"
    assert "far_above_historical_low" in result.reasons
    assert "out_of_stock" in result.reasons


def test_deal_score_engine_returns_watch_for_middle_case():
    result = DealScoreEngine().calculate(
        DealScoreInput(
            current_amount=Decimal("879.00"),
            lowest_90d_amount=Decimal("849.00"),
            cross_store_min_amount=Decimal("849.00"),
            store_trust_score=80,
            stock_status="in_stock",
        )
    )

    assert 60 <= result.score < 80
    assert result.decision == "WATCH"


def test_deal_score_serializer():
    result = DealScoreEngine().calculate(
        DealScoreInput(
            current_amount=Decimal("849.00"),
            lowest_90d_amount=Decimal("849.00"),
            cross_store_min_amount=Decimal("849.00"),
            store_trust_score=95,
            stock_status="in_stock",
        )
    )

    data = serialize_deal_score_result(result)

    assert data["decision"] == "BUY"
    assert isinstance(data["score"], int)
    assert isinstance(data["reasons"], list)
