from app.domains.trust_intelligence.trust_engine import TrustIntelligenceEngine
from app.domains.trust_intelligence.trust_models import TrustSignal
from app.domains.trust_intelligence.trust_serializer import serialize_trust_profile


def test_trust_serializer_serializes_profile():
    profile = TrustIntelligenceEngine().build_profile(
        entity_type="product",
        entity_id="product-1",
        signal=TrustSignal(source_type="product", source_id="product-1", positive_count=5, total_count=5),
    )

    data = serialize_trust_profile(profile)

    assert data["entity_type"] == "product"
    assert data["entity_id"] == "product-1"
    assert data["trust_score"] == 100
