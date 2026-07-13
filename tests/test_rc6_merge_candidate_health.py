import pytest

from app.domains.products.intelligence.merge_candidate_health import MergeCandidateHealthService


class FakeRepository:
    def __init__(self, counts):
        self.counts = counts

    async def count_by_status(self, status):
        return self.counts.get(status, 0)


@pytest.mark.asyncio
async def test_merge_candidate_health_passes_for_normal_queue():
    result = await MergeCandidateHealthService(
        FakeRepository({
            "PENDING": 2,
            "APPROVED": 1,
            "APPLIED": 4,
            "REJECTED": 0,
            "NEEDS_REVIEW": 1,
        })
    ).check()

    assert result["name"] == "merge_candidate_queue"
    assert result["passed"] is True
    assert result["data"]["pending_count"] == 2
    assert result["data"]["approved_count"] == 1


@pytest.mark.asyncio
async def test_merge_candidate_health_fails_when_too_many_approved_waiting():
    result = await MergeCandidateHealthService(
        FakeRepository({
            "APPROVED": 101,
        })
    ).check()

    assert result["passed"] is False
    assert result["error"] == "too_many_approved_merge_candidates_waiting_apply"
