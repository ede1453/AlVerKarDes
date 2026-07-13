from app.domains.deal_notifications.service import DealAlertEligibilityEngine


def test_rc206_eligible_deal():
    result = DealAlertEligibilityEngine().evaluate(
        deal={
            "decision":"BUY",
            "confidence_score":85,
            "observed_discount_pct":25,
            "freshness_status":"FRESH",
            "anomaly_detected":False,
        }
    )
    assert result["eligible"] is True

def test_rc206_reject_low_confidence():
    result = DealAlertEligibilityEngine().evaluate(
        deal={
            "decision":"BUY",
            "confidence_score":40,
            "observed_discount_pct":25,
            "freshness_status":"FRESH",
        }
    )
    assert result["eligible"] is False
    assert "CONFIDENCE_TOO_LOW" in result["reasons"]
