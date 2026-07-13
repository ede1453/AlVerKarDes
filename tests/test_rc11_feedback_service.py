import pytest

from app.domains.feedback_learning.feedback_repository import InMemoryFeedbackRepository
from app.domains.feedback_learning.feedback_service import FeedbackLearningService


@pytest.mark.asyncio
async def test_feedback_service_submits_and_summarizes_user_feedback():
    service = FeedbackLearningService(repository=InMemoryFeedbackRepository())

    saved = await service.submit_feedback(
        {
            "user_id": "user-1",
            "decision_id": "decision-1",
            "feedback_type": "HELPFUL",
            "rating": 5,
        }
    )

    assert saved["feedback_type"] == "HELPFUL"

    summary = await service.summarize_user_feedback("user-1")

    assert summary["learning_signal"] == "POSITIVE"
    assert summary["total_feedback_count"] == 1
