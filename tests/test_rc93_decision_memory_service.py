import pytest

from app.domains.decision_memory.decision_memory_repository import InMemoryDecisionMemoryRepository
from app.domains.decision_memory.decision_memory_service import DecisionMemoryService


@pytest.mark.asyncio
async def test_decision_memory_service_stores_and_evaluates_outcome():
    service = DecisionMemoryService(repository=InMemoryDecisionMemoryRepository())

    saved = await service.store(
        {
            "offer_id": "offer-1",
            "final_decision": "BUY_NOW",
            "confidence": 94,
            "reason_codes": ["STRONG_BUY_SIGNAL"],
        }
    )

    updated = await service.evaluate_outcome(
        saved["id"],
        {
            "decision_price": "100.00",
            "future_price": "120.00",
        },
    )

    assert updated["outcome"]["decision_correct"] is True
    assert updated["outcome"]["learning_signal"] == "POSITIVE"
