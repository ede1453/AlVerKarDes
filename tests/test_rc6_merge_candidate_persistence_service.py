import pytest

from app.domains.products.intelligence.merge_candidate_persistence_service import MergeCandidatePersistenceService


class Saved:
    def __init__(self, id):
        self.id = id


class FakeRepository:
    def __init__(self):
        self.items = []

    async def create_from_candidate(self, candidate):
        saved = Saved(id=f"saved-{len(self.items)+1}")
        self.items.append(candidate)
        return saved


class DummyDB:
    pass


@pytest.mark.asyncio
async def test_merge_candidate_persistence_service_saves_candidates():
    service = MergeCandidatePersistenceService(DummyDB())
    service.repository = FakeRepository()

    result = await service.build_and_persist(
        country="DE",
        offers=[
            {"source": "amazon-de", "title": "Apple MacBook Air M5 16GB 512GB Midnight"},
            {"source": "mediamarkt-de", "title": "Apple MBA M5 16/512 Silver"},
        ],
    )

    assert result["candidate_count"] == 1
    assert result["saved_count"] == 1
    assert result["saved_ids"] == ["saved-1"]
