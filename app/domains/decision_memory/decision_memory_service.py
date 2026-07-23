from decimal import Decimal

from app.domains.decision_memory.decision_memory_engine import DecisionMemoryEngine
from app.domains.decision_memory.decision_memory_repository import DecisionMemoryRepository
from app.domains.decision_memory.decision_memory_serializer import serialize_decision_memory
from app.domains.decision_memory.learning_engine import DecisionLearningEngine


class DecisionMemoryService:
    def __init__(
        self,
        repository: DecisionMemoryRepository | None = None,
        engine: DecisionMemoryEngine | None = None,
        learning_engine: DecisionLearningEngine | None = None,
    ):
        self.repository = repository or DecisionMemoryRepository()
        self.engine = engine or DecisionMemoryEngine()
        self.learning_engine = learning_engine or DecisionLearningEngine()

    async def store(self, payload: dict):
        record = self.engine.create_record(payload)
        saved = await self.repository.save(record)
        return serialize_decision_memory(saved)

    async def get(self, decision_id: str):
        record = await self.repository.get(decision_id)
        if record is None:
            return None
        return serialize_decision_memory(record)

    async def evaluate_outcome(self, decision_id: str, payload: dict):
        record = await self.repository.get(decision_id)
        if record is None:
            return None

        outcome = self.learning_engine.evaluate_outcome(
            final_decision=record.final_decision,
            decision_price=Decimal(str(payload["decision_price"])),
            future_price=Decimal(str(payload["future_price"])),
        )

        updated = await self.repository.update_outcome(decision_id, outcome)
        return serialize_decision_memory(updated)

    async def get_user_history_summary(self, user_id: str, limit: int = 5) -> dict:
        records = await self.repository.list_recent_by_user(user_id, limit=limit)
        return self.engine.summarize(records)
