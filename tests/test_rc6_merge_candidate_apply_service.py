from uuid import uuid4

import pytest

from app.domains.products.intelligence.merge_candidate_apply_service import MergeCandidateApplyService


class Candidate:
    def __init__(self, status="APPROVED", decision="AUTO_MERGE"):
        self.id = uuid4()
        self.signature = "apple::macbook air::m5::16gb::512gb::de"
        self.decision = decision
        self.status = status


class FakeRepository:
    def __init__(self, candidate):
        self.candidate = candidate

    async def get_by_id(self, candidate_id):
        if self.candidate and candidate_id == self.candidate.id:
            return self.candidate
        return None

    async def mark_applied(self, candidate_id):
        self.candidate.status = "APPLIED"
        return self.candidate


@pytest.mark.asyncio
async def test_apply_service_applies_approved_auto_merge_candidate():
    candidate = Candidate(status="APPROVED", decision="AUTO_MERGE")
    service = MergeCandidateApplyService(FakeRepository(candidate))

    result = await service.apply(candidate_id=candidate.id)

    assert result["applied"] is True
    assert result["status"] == "APPLIED"


@pytest.mark.asyncio
async def test_apply_service_rejects_missing_candidate():
    candidate = Candidate(status="APPROVED", decision="AUTO_MERGE")
    service = MergeCandidateApplyService(FakeRepository(candidate))

    with pytest.raises(ValueError, match="merge_candidate_not_found"):
        await service.apply(candidate_id=uuid4())


@pytest.mark.asyncio
async def test_apply_service_rejects_not_approved_candidate():
    candidate = Candidate(status="PENDING", decision="AUTO_MERGE")
    service = MergeCandidateApplyService(FakeRepository(candidate))

    with pytest.raises(ValueError, match="merge_candidate_not_approved"):
        await service.apply(candidate_id=candidate.id)


@pytest.mark.asyncio
async def test_apply_service_rejects_non_auto_merge_candidate():
    candidate = Candidate(status="APPROVED", decision="REVIEW")
    service = MergeCandidateApplyService(FakeRepository(candidate))

    with pytest.raises(ValueError, match="merge_candidate_not_auto_merge"):
        await service.apply(candidate_id=candidate.id)
