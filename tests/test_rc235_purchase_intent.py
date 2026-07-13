from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc235_purchase_intent():
    result = ConsumerTrustService().record_purchase_intent(
        user_id="u1",
        deal_id="d1",
        intent_level="HIGH",
    )
    assert result["intent"]["intent_level"] == "HIGH"
