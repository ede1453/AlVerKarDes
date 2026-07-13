class InMemoryLLMAuditTraceRepository:
    def __init__(self):
        self.records = {}

    async def save(self, record):
        self.records[record.id] = record
        return record

    async def get(self, trace_id: str):
        return self.records.get(trace_id)

    async def list_recent(self, limit: int = 20):
        records = sorted(
            self.records.values(),
            key=lambda record: record.created_at,
            reverse=True,
        )
        return records[:limit]


class LLMAuditTraceRepository(InMemoryLLMAuditTraceRepository):
    def __init__(self, db=None):
        super().__init__()
        self.db = db
