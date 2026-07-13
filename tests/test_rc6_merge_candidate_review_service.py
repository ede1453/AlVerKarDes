from uuid import uuid4

import pytest

from app.domains.products.intelligence.merge_candidate_review_service import MergeCandidateReviewService


class Candidate:
    def __init__(self, id):
        self.id = id
        self.signature = "test::signature"
        self.decision = "REVIEW"
        self.status = "PENDING"


class FakeRepository:
    def __init__(self):
        self.candidate = Candidate(uuid4())
        self.updated = None

    async def update_status(self, candidate_id, status):
        if candidate_id != self.candidate.id:
            return None
        self.candidate.status = status
        self.updated = status
        return self.candidate


@pytest.mark.asyncio
async def test_review_service_approves_candidate():
    repo = FakeRepository()

    result = await MergeCandidateReviewService(repo).review(
        candidate_id=repo.candidate.id,
        status="approved",
    )

    assert result.status == "APPROVED"
    assert repo.updated == "APPROVED"


@pytest.mark.asyncio
async def test_review_service_rejects_invalid_status():
    repo = FakeRepository()

    with pytest.raises(ValueError, match="invalid_merge_candidate_status"):
        await MergeCandidateReviewService(repo).review(
            candidate_id=repo.candidate.id,
            status="done",
        )


@pytest.mark.asyncio
async def test_review_service_rejects_missing_candidate():
    repo = FakeRepository()

    with pytest.raises(ValueError, match="merge_candidate_not_found"):
        await MergeCandidateReviewService(repo).review(
            candidate_id=uuid4(),
            status="APPROVED",
        )
