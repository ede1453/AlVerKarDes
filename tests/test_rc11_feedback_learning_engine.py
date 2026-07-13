from app.domains.feedback_learning.feedback_engine import FeedbackEngine
from app.domains.feedback_learning.feedback_learning_engine import FeedbackLearningEngine


def test_feedback_learning_engine_returns_positive_signal():
    records = [
        FeedbackEngine().create_record({"user_id": "user-1", "feedback_type": "HELPFUL", "rating": 5}),
        FeedbackEngine().create_record({"user_id": "user-1", "feedback_type": "PURCHASED", "rating": 5}),
    ]

    summary = FeedbackLearningEngine().summarize(records)

    assert summary.learning_signal == "POSITIVE"
    assert summary.confidence_adjustment > 0


def test_feedback_learning_engine_returns_negative_signal():
    records = [
        FeedbackEngine().create_record({"user_id": "user-1", "feedback_type": "NOT_HELPFUL", "rating": 1}),
        FeedbackEngine().create_record({"user_id": "user-1", "feedback_type": "IGNORED"}),
    ]

    summary = FeedbackLearningEngine().summarize(records)

    assert summary.learning_signal == "NEGATIVE"
    assert summary.confidence_adjustment < 0
