from app.domains.deals.deal_score_engine import DealScoreEngine, DealScoreInput
from app.domains.deals.deal_score_serializer import serialize_deal_score_result
from app.domains.deals.lowest_price_engine import LowestPriceEngine
from app.domains.deals.lowest_price_serializer import serialize_lowest_price_report


class DealSummaryService:
    def __init__(self):
        self.lowest_price_engine = LowestPriceEngine()
        self.deal_score_engine = DealScoreEngine()

    def summarize(
        self,
        *,
        prices: list,
        cross_store_min_amount=None,
        store_trust_score=None,
        stock_status="in_stock",
        now=None,
    ):
        lowest_report = self.lowest_price_engine.calculate(prices, now=now)

        if lowest_report.current_amount is None:
            return {
                "has_price_data": False,
                "lowest_prices": serialize_lowest_price_report(lowest_report),
                "deal_score": None,
                "recommendation": "NO_PRICE_DATA",
                "message": "Price data is not available yet.",
            }

        score_result = self.deal_score_engine.calculate(
            DealScoreInput(
                current_amount=lowest_report.current_amount,
                lowest_30d_amount=lowest_report.lowest_30d.amount,
                lowest_90d_amount=lowest_report.lowest_90d.amount,
                all_time_low_amount=lowest_report.lowest_all_time.amount,
                cross_store_min_amount=cross_store_min_amount,
                store_trust_score=store_trust_score,
                stock_status=stock_status,
            )
        )

        return {
            "has_price_data": True,
            "lowest_prices": serialize_lowest_price_report(lowest_report),
            "deal_score": serialize_deal_score_result(score_result),
            "recommendation": score_result.decision,
            "message": self._message_for_decision(score_result.decision),
        }

    def _message_for_decision(self, decision: str) -> str:
        if decision == "BUY":
            return "This looks like a strong deal compared with recent price history."
        if decision == "WATCH":
            return "This is a reasonable offer, but watching for a better price may be worthwhile."
        return "This does not look like a strong deal right now."
