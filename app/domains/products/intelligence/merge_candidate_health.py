class MergeCandidateHealthService:
    def __init__(self, repository):
        self.repository = repository

    async def check(self):
        pending_count = await self.repository.count_by_status("PENDING")
        approved_count = await self.repository.count_by_status("APPROVED")
        applied_count = await self.repository.count_by_status("APPLIED")
        rejected_count = await self.repository.count_by_status("REJECTED")
        needs_review_count = await self.repository.count_by_status("NEEDS_REVIEW")

        # RC6 rule: queue is healthy unless approved items accumulate too much.
        passed = approved_count <= 100

        return {
            "name": "merge_candidate_queue",
            "passed": passed,
            "data": {
                "pending_count": pending_count,
                "approved_count": approved_count,
                "applied_count": applied_count,
                "rejected_count": rejected_count,
                "needs_review_count": needs_review_count,
            },
            "error": None if passed else "too_many_approved_merge_candidates_waiting_apply",
        }
