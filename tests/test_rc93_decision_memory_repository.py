import pytest

from app.domains.decision_memory.decision_memory_engine import DecisionMemoryEngine
from app.domains.decision_memory.decision_memory_repository import InMemoryDecisionMemoryRepository


@pytest.mark.asyncio
async def test_decision_memory_repository_saves_and_reads_record():
    repo = InMemoryDecisionMemoryRepository()
    record = DecisionMemoryEngine().create_record(
        {
            "final_decision": "BUY_NOW",
            "confidence": 94,
        }
    )

    saved = await repo.save(record)
    found = await repo.get(saved.id)

    assert found.id == saved.id
    assert found.final_decision == "BUY_NOW"
