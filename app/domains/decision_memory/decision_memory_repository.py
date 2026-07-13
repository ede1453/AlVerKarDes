class InMemoryDecisionMemoryRepository:
    def __init__(self):
        self.records = {}

    async def save(self, record):
        self.records[record.id] = record
        return record

    async def get(self, decision_id: str):
        return self.records.get(decision_id)

    async def update_outcome(self, decision_id: str, outcome: dict):
        record = self.records.get(decision_id)
        if record is None:
            return None

        record.outcome = outcome
        return record


class DecisionMemoryRepository(InMemoryDecisionMemoryRepository):
    """
    Compatibility repository.

    This initial RC uses an in-memory implementation for tests and API contract.
    A DB-backed implementation can later replace this class without changing
    service/API contracts.
    """

    def __init__(self, db=None):
        super().__init__()
        self.db = db
