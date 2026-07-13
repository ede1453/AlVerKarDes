import pytest

from app.domains.trust_intelligence.trust_models import TrustSignal
from app.domains.trust_intelligence.trust_repository import InMemoryTrustRepository


@pytest.mark.asyncio
async def test_trust_repository_saves_and_reads_signal():
    repo = InMemoryTrustRepository()
    signal = TrustSignal(source_type="store", source_id="store-1", positive_count=5, total_count=5)

    await repo.save_signal(signal)
    found = await repo.get_signal("store", "store-1")

    assert found.source_id == "store-1"
    assert found.positive_count == 5
