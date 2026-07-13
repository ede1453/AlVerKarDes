from app.domains.feedback_learning.feedback_models import (
    DecisionFeedbackCreate,
    create_feedback_record,
)


class FeedbackEngine:
    VALID_FEEDBACK_TYPES = {
        "HELPFUL",
        "NOT_HELPFUL",
        "PURCHASED",
        "IGNORED",
        "PRICE_TOO_HIGH",
        "WRONG_RECOMMENDATION",
    }

    def create_record(self, payload: dict):
        feedback_type = payload.get("feedback_type", "HELPFUL")
        if feedback_type not in self.VALID_FEEDBACK_TYPES:
            feedback_type = "HELPFUL"

        return create_feedback_record(
            DecisionFeedbackCreate(
                user_id=payload["user_id"],
                decision_id=payload.get("decision_id"),
                product_id=payload.get("product_id"),
                offer_id=payload.get("offer_id"),
                feedback_type=feedback_type,
                rating=payload.get("rating"),
                comment=payload.get("comment"),
                metadata=payload.get("metadata", {}),
            )
        )
