class InMemoryFeedbackRepository:
    def __init__(self):
        self.records = {}

    async def save(self, record):
        self.records[record.id] = record
        return record

    async def get(self, feedback_id: str):
        return self.records.get(feedback_id)

    async def list_for_user(self, user_id: str):
        return [record for record in self.records.values() if record.user_id == user_id]

    async def list_for_decision(self, decision_id: str):
        return [record for record in self.records.values() if record.decision_id == decision_id]


class FeedbackRepository(InMemoryFeedbackRepository):
    def __init__(self, db=None):
        super().__init__()
        self.db = db
