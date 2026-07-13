import pytest

from app.domains.feedback_learning.feedback_engine import FeedbackEngine
from app.domains.feedback_learning.feedback_repository import InMemoryFeedbackRepository


@pytest.mark.asyncio
async def test_feedback_repository_saves_and_lists_records():
    repo = InMemoryFeedbackRepository()
    record = FeedbackEngine().create_record(
        {
            "user_id": "user-1",
            "decision_id": "decision-1",
            "feedback_type": "HELPFUL",
        }
    )

    saved = await repo.save(record)
    found = await repo.get(saved.id)
    user_records = await repo.list_for_user("user-1")
    decision_records = await repo.list_for_decision("decision-1")

    assert found.id == saved.id
    assert len(user_records) == 1
    assert len(decision_records) == 1
