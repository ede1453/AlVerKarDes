import pytest

from app.domains.trust_intelligence.trust_repository import InMemoryTrustRepository
from app.domains.trust_intelligence.trust_service import TrustIntelligenceService


@pytest.mark.asyncio
async def test_trust_service_upserts_signal_and_evaluates():
    service = TrustIntelligenceService(repository=InMemoryTrustRepository())

    await service.upsert_signal(
        {
            "source_type": "store",
            "source_id": "store-1",
            "positive_count": 10,
            "negative_count": 0,
            "total_count": 10,
        }
    )

    result = await service.evaluate(
        {
            "decision_id": "decision-1",
            "store_id": "store-1",
            "base_confidence": 90,
            "final_decision": "BUY_NOW",
        }
    )

    assert result["store_score"] >= 85
    assert result["final_confidence"] > 90
    assert "HIGH_STORE_TRUST" in result["reason_codes"]
