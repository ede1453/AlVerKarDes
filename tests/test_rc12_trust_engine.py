from app.domains.trust_intelligence.trust_engine import TrustIntelligenceEngine
from app.domains.trust_intelligence.trust_models import TrustEvaluationInput, TrustSignal


def test_trust_engine_builds_profile_from_positive_signal():
    profile = TrustIntelligenceEngine().build_profile(
        entity_type="store",
        entity_id="store-1",
        signal=TrustSignal(
            source_type="store",
            source_id="store-1",
            positive_count=9,
            negative_count=1,
            total_count=10,
        ),
    )

    assert profile.trust_score >= 80
    assert profile.reliability_score >= 90


def test_trust_engine_reduces_confidence_for_low_trust_store():
    engine = TrustIntelligenceEngine()
    low_store = engine.build_profile(
        entity_type="store",
        entity_id="store-1",
        signal=TrustSignal(
            source_type="store",
            source_id="store-1",
            positive_count=1,
            negative_count=9,
            fraud_count=1,
            total_count=10,
        ),
    )

    result = engine.evaluate(
        data=TrustEvaluationInput(
            decision_id="decision-1",
            base_confidence=90,
            final_decision="BUY_NOW",
        ),
        store_profile=low_store,
    )

    assert result.final_confidence < 90
    assert result.risk_modifier == "HIGH_RISK"
    assert "LOW_STORE_TRUST" in result.reason_codes
