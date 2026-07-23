from decimal import Decimal

from app.domains.price_history.price_history_models import PriceHistorySummary


class PriceHistoryEngine:
    def summarize(self, *, product_key: str, points: list) -> PriceHistorySummary:
        if not points:
            return PriceHistorySummary(
                product_key=product_key,
                currency=None,
                point_count=0,
                min_price=None,
                max_price=None,
                average_price=None,
                latest_price=None,
                trend="UNKNOWN",
                points=[],
            )

        prices = [point.price for point in points]
        currencies = list(dict.fromkeys([point.currency for point in points]))
        latest_price = points[-1].price
        first_price = points[0].price

        if latest_price < first_price:
            trend = "DOWN"
        elif latest_price > first_price:
            trend = "UP"
        else:
            trend = "FLAT"

        return PriceHistorySummary(
            product_key=product_key,
            currency=currencies[0] if len(currencies) == 1 else None,
            point_count=len(points),
            min_price=min(prices),
            max_price=max(prices),
            average_price=sum(prices, Decimal("0")) / Decimal(len(prices)),
            latest_price=latest_price,
            trend=trend,
            points=points,
        )
