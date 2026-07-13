from uuid import UUID


class MergeCandidateApplyService:
    def __init__(self, repository):
        self.repository = repository

    async def apply(self, *, candidate_id: UUID):
        candidate = await self.repository.get_by_id(candidate_id)

        if not candidate:
            raise ValueError("merge_candidate_not_found")

        if candidate.status != "APPROVED":
            raise ValueError("merge_candidate_not_approved")

        if candidate.decision != "AUTO_MERGE":
            raise ValueError("merge_candidate_not_auto_merge")

        applied = await self.repository.mark_applied(candidate_id)

        return {
            "id": str(applied.id),
            "signature": applied.signature,
            "decision": applied.decision,
            "status": applied.status,
            "applied": True,
        }
