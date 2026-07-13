from app.domains.decision_memory.decision_memory_engine import DecisionMemoryEngine


def test_decision_memory_engine_creates_record():
    record = DecisionMemoryEngine().create_record(
        {
            "product_id": "product-1",
            "offer_id": "offer-1",
            "final_decision": "BUY_NOW",
            "confidence": 94,
            "deal_score": 95,
            "authenticity_score": 96,
            "reason_codes": ["STRONG_BUY_SIGNAL"],
        }
    )

    assert record.id
    assert record.final_decision == "BUY_NOW"
    assert record.confidence == 94
    assert record.reason_codes == ["STRONG_BUY_SIGNAL"]
