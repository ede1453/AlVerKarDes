from uuid import UUID


class MergeCandidateReviewService:
    ALLOWED_STATUSES = {"APPROVED", "REJECTED", "NEEDS_REVIEW"}

    def __init__(self, repository):
        self.repository = repository

    async def review(self, *, candidate_id: UUID, status: str):
        normalized_status = status.upper().strip()

        if normalized_status not in self.ALLOWED_STATUSES:
            raise ValueError("invalid_merge_candidate_status")

        candidate = await self.repository.update_status(candidate_id, normalized_status)

        if not candidate:
            raise ValueError("merge_candidate_not_found")

        return candidate
