from app.domains.feedback_learning.feedback_engine import FeedbackEngine


def test_feedback_engine_creates_feedback_record():
    record = FeedbackEngine().create_record(
        {
            "user_id": "user-1",
            "decision_id": "decision-1",
            "feedback_type": "HELPFUL",
            "rating": 5,
        }
    )

    assert record.id
    assert record.user_id == "user-1"
    assert record.feedback_type == "HELPFUL"
    assert record.rating == 5


def test_feedback_engine_normalizes_unknown_feedback_type():
    record = FeedbackEngine().create_record(
        {
            "user_id": "user-1",
            "feedback_type": "UNKNOWN",
        }
    )

    assert record.feedback_type == "HELPFUL"
