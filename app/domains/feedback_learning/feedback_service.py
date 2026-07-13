from app.domains.feedback_learning.feedback_engine import FeedbackEngine
from app.domains.feedback_learning.feedback_learning_engine import FeedbackLearningEngine
from app.domains.feedback_learning.feedback_repository import FeedbackRepository
from app.domains.feedback_learning.feedback_serializer import (
    serialize_feedback,
    serialize_feedback_learning_summary,
)


class FeedbackLearningService:
    def __init__(
        self,
        repository: FeedbackRepository | None = None,
        feedback_engine: FeedbackEngine | None = None,
        learning_engine: FeedbackLearningEngine | None = None,
    ):
        self.repository = repository or FeedbackRepository()
        self.feedback_engine = feedback_engine or FeedbackEngine()
        self.learning_engine = learning_engine or FeedbackLearningEngine()

    async def submit_feedback(self, payload: dict):
        record = self.feedback_engine.create_record(payload)
        saved = await self.repository.save(record)
        return serialize_feedback(saved)

    async def get_feedback(self, feedback_id: str):
        record = await self.repository.get(feedback_id)
        if record is None:
            return None
        return serialize_feedback(record)

    async def summarize_user_feedback(self, user_id: str):
        records = await self.repository.list_for_user(user_id)
        summary = self.learning_engine.summarize(records)
        return serialize_feedback_learning_summary(summary)

    async def summarize_decision_feedback(self, decision_id: str):
        records = await self.repository.list_for_decision(decision_id)
        summary = self.learning_engine.summarize(records)
        return serialize_feedback_learning_summary(summary)
