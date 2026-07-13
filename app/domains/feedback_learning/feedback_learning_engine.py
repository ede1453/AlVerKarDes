from app.domains.feedback_learning.feedback_models import FeedbackLearningSummary


class FeedbackLearningEngine:
    def summarize(self, records) -> FeedbackLearningSummary:
        records = list(records)
        total = len(records)

        helpful_count = self._count(records, "HELPFUL")
        not_helpful_count = self._count(records, "NOT_HELPFUL") + self._count(records, "WRONG_RECOMMENDATION")
        purchased_count = self._count(records, "PURCHASED")
        ignored_count = self._count(records, "IGNORED")

        ratings = [record.rating for record in records if record.rating is not None]
        average_rating = None if not ratings else sum(ratings) / len(ratings)

        learning_signal, adjustment, reasons = self._signal(
            total=total,
            helpful_count=helpful_count,
            not_helpful_count=not_helpful_count,
            purchased_count=purchased_count,
            ignored_count=ignored_count,
            average_rating=average_rating,
        )

        return FeedbackLearningSummary(
            total_feedback_count=total,
            helpful_count=helpful_count,
            not_helpful_count=not_helpful_count,
            purchased_count=purchased_count,
            ignored_count=ignored_count,
            average_rating=average_rating,
            learning_signal=learning_signal,
            confidence_adjustment=adjustment,
            reason_codes=reasons,
        )

    def _count(self, records, feedback_type: str) -> int:
        return sum(1 for record in records if record.feedback_type == feedback_type)

    def _signal(
        self,
        *,
        total: int,
        helpful_count: int,
        not_helpful_count: int,
        purchased_count: int,
        ignored_count: int,
        average_rating: float | None,
    ):
        if total == 0:
            return "NEUTRAL", 0, ["NO_FEEDBACK"]

        positive = helpful_count + purchased_count
        negative = not_helpful_count + ignored_count

        if average_rating is not None and average_rating >= 4:
            positive += 1

        if average_rating is not None and average_rating <= 2:
            negative += 1

        if positive > negative:
            return "POSITIVE", min(10, positive * 2), ["POSITIVE_USER_FEEDBACK"]

        if negative > positive:
            return "NEGATIVE", -min(10, negative * 2), ["NEGATIVE_USER_FEEDBACK"]

        return "MIXED", 0, ["MIXED_USER_FEEDBACK"]
